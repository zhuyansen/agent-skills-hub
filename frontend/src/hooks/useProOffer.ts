import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";
import { CHECKOUT_LINKS, USD_PRICING } from "../lib/checkout";

export function useProOffer() {
  const [soldOut, setSoldOut] = useState(false);
  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const result = await supabase?.rpc("pro_early_bird_status");
        if (alive && result && !result.error && typeof result.data?.sold_out === "boolean") {
          setSoldOut(result.data.sold_out);
        }
      } catch { /* Stripe also enforces the cap if the status request fails. */ }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 60_000);
    return () => { alive = false; window.clearInterval(timer); };
  }, []);
  return { soldOut, price: soldOut ? USD_PRICING.proStandard : USD_PRICING.proEarly,
    link: soldOut ? CHECKOUT_LINKS.proStandard : CHECKOUT_LINKS.pro };
}
