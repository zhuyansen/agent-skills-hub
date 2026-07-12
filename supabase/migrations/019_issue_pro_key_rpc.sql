-- 019_issue_pro_key_rpc.sql
-- 让 jasonzhu.ai 付款成功后自动发码:一个共享密钥保护的 SECURITY DEFINER RPC。
-- 镜像 ops/issue_member_key.py 的逻辑(同样的 key 前缀 ash_pro_、sha256 存储、1 年有效期),
-- 唯一区别是可以被 jasonzhu.ai 后端跨站调用。
--
-- 安全模型:
--   - p_secret 是唯一准入凭证。本文件只含它的 sha256(v_expected_secret_hash,单向不可逆,
--     入库/入 git 都安全);原始密钥只交给 jasonzhu.ai 一份(写在它的 .env.local,不进 git)。
--   - 轮换:生成新密钥 → 把新密钥的 sha256 hex 替换进 v_expected_secret_hash → 重跑本文件
--     (CREATE OR REPLACE),不影响已发出的 key。
--   - GRANT 给 anon 是安全的:没有正确 p_secret,anon 调用什么也拿不到。
--   - 返回明文 key 只此一次;表里只存 hash。
--   - 幂等:付款 webhook 会重试。带 p_order_id 时,同一订单重复调用不会重复发码
--     (返回 already_issued);首次那把明文 key 才是发给买家的那把。
--   - 早鸟名额:'早鸟199' 仅在 <100 时发放;满 100 静默降级为 '标准365' 并回报实际档位。

-- ── member_keys: 加 source + order_id(幂等) ──────────────────
ALTER TABLE member_keys ADD COLUMN IF NOT EXISTS source   text;
ALTER TABLE member_keys ADD COLUMN IF NOT EXISTS order_id text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_member_keys_order_id
  ON member_keys (order_id) WHERE order_id IS NOT NULL;

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

CREATE OR REPLACE FUNCTION issue_pro_key(
  p_secret   text,
  p_email    text,
  p_note     text DEFAULT '标准365',
  p_order_id text DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  v_expected_secret_hash text := '332a0e4d55027893bc48f2513c8cc9dfe9fcb68ff1ba1a01f2367b01406f0d20';
  v_note      text := COALESCE(NULLIF(p_note, ''), '标准365');
  v_existing  record;
  v_earlybird int;
  v_downgrade boolean := false;
  v_raw_key   text;
BEGIN
  -- 1. 密钥准入
  IF p_secret IS NULL OR encode(sha256(p_secret::bytea), 'hex') <> v_expected_secret_hash THEN
    RAISE EXCEPTION 'invalid_secret' USING errcode = '42501';
  END IF;

  IF p_email IS NULL OR p_email !~ '^[^\s@]+@[^\s@]+\.[^\s@]+$' THEN
    RAISE EXCEPTION 'invalid_email' USING errcode = '22023';
  END IF;

  -- 2. 幂等:同订单不重复发码
  IF p_order_id IS NOT NULL THEN
    SELECT email, tier, note INTO v_existing FROM member_keys WHERE order_id = p_order_id;
    IF FOUND THEN
      RETURN json_build_object('status', 'already_issued', 'note', v_existing.note);
    END IF;
  END IF;

  -- 3. 早鸟名额:100 个后降级标准价
  IF v_note = '早鸟199' THEN
    SELECT count(*) INTO v_earlybird FROM member_keys WHERE note = '早鸟199';
    IF v_earlybird >= 100 THEN
      v_note := '标准365';
      v_downgrade := true;
    END IF;
  END IF;

  -- 4. 发码:表内只存 hash,明文只返回一次
  v_raw_key := 'ash_pro_' || translate(encode(gen_random_bytes(24), 'base64'), '+/=', '-_');
  INSERT INTO member_keys (key_hash, email, tier, expires_at, note, source, order_id)
  VALUES (encode(sha256(v_raw_key::bytea), 'hex'), p_email, 'pro',
          now() + interval '1 year', v_note, 'jasonzhu.ai', p_order_id);

  RETURN json_build_object(
    'status', 'issued',
    'key', v_raw_key,
    'note', v_note,
    'downgraded_to_standard', v_downgrade,
    'expires_at', (now() + interval '1 year')
  );
END;
$$;

-- 旧签名(3 参)在增加 p_order_id 后仍可能残留 —— 显式清掉,避免 PostgREST 歧义
DROP FUNCTION IF EXISTS issue_pro_key(text, text, text);

GRANT EXECUTE ON FUNCTION issue_pro_key(text, text, text, text) TO anon, authenticated;
