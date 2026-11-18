# Morning Loaf: how an online order flows

An animated diagram of how an online order at Morning Loaf, a small bakery, moves through the business:

Customer → Website → Payment (Stripe) → Order queue → Oven (bakes at 4 a.m.) → Courier → Customer

- The steps appear in this order, and a dot travels along each arrow to the next step.
- From Payment, a second path: if the payment fails, an arrow goes to "Email: retry payment", and from there back to Payment.
- Every label is readable.

Deliver one self-contained file, ~/work/output/index.html.

preview.mp4: 1920 x 1080, 12 seconds of the diagram playing from the start.
