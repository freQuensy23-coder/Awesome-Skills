# Treblo accounts, credits, and exhausted-account options

Public sources checked **2026-09-08**. This is an operational guide, not a promise of future pricing, eligibility, or availability. Historical observations below were supplied from verified runs on **2026-09-07–08**; they were not repeated during this documentation review. No paid inference or new account creation was performed for this review.

## Start with one legitimate account

1. Open [Treblo Developers](https://treblo.com/developers) and choose **Get Started Free**, which leads to the normal [signup page](https://treblo.com/login?redirectUrl=%2Fdevelopers%2Faccount&mode=signup). Read the [Terms of Service](https://treblo.com/tos), [API Terms](https://treblo.com/api-terms), and [Privacy Policy](https://treblo.com/privacy) before accepting them. The Terms require users to be at least 18.
2. Use your own identity and normal authentication. The public signup page currently offers Google, Discord, Apple, and email/password. Google OAuth signup was verified historically. Complete any Google login or two-factor authentication yourself; an assistant should pause for that interaction, not request exported cookies or session tokens.
3. Open the [developer account page](https://treblo.com/developers/account), locate API-key management, and create a descriptively named key. UI labels and provisioning timing can change. Creating a key accepts the API Terms; do not create unnecessary replacement keys to seek credits.
4. Store the key in a secret manager and inject it as `TREBLO_API_KEY` into the process environment. Do not put it in source code, chat prompts, shell-history command arguments, URLs, repositories, or logs. API authentication is `Authorization: Bearer …`; browser cookies are not the public API authentication method.
5. Read `GET https://api.treblo.com/v1/credits/balance` before generating. See the read-only Python example in [api.md](api.md). Inspect both `num_credits` (documented as subscription credits) and `num_credits_payg` (purchased credits). Do not infer the usable API balance from a website badge alone.

**Historical provisioning observation — 2026-09-07:** after Google signup, the developer Plan display initially showed **0**. Creating the first named API key activated **1,500 free credits**, confirmed with the balance endpoint. No payment card was required. This does not establish that key creation always triggers activation, that every signup qualifies, or that creating more keys adds credits. If the advertised trial is missing, refresh the authenticated developer dashboard, read the balance, and contact official support rather than creating more accounts.

## Public API pricing checked on 2026-09-08

The [API pricing page](https://treblo.com/developers/pricing) states:

| Offer | Advertised price | Included credits | Listed pay-as-you-go rate |
| --- | --- | --- | --- |
| Free Trial | No credit card required | 1,500 on signup | Not specified in the trial block |
| Starter | $11/month | 20,000/month | $0.06 per 100 credits |
| Pro | $88/month | 160,000/month | $0.06 per 100 credits |
| Scale | $330/month | 660,000/month | $0.05 per 100 credits |
| Enterprise | $1,150/month | 2,875,000/month | $0.04 per 100 credits |

The page advertises full trial API access, including v2 and v3. It says **one song costs 100 credits; `num_songs=2` costs 150 credits**. Those costs also match historical v2 observations. v3 always generates one song; the two-song setting is v2-specific. Prices and feature costs can change. Check the active account's checkout and current endpoint pricing before authorizing a job; a failed edit may still require billing reconciliation rather than assumptions about a refund.

A **$5 minimum top-up** was observed historically. The public pricing page reviewed here does **not** establish that minimum or a standalone free-account pay-as-you-go rate. Verify both in the live checkout, obtain explicit budget approval, and have the user complete the purchase. Do not silently subscribe or enable automatic top-up.

### Which credits reset?

[API Terms §8](https://treblo.com/api-terms), dated **2026-08-20**, specify:

- Subscription credits are set to the plan allowance at the start of each **billing period**, not an invented daily reset. They do not roll over and can lapse on plan changes, cancellation, lapse, or termination.
- Purchased pay-as-you-go credits do not expire and are unaffected by plan changes or cancellation.
- Subscription credits are consumed before pay-as-you-go credits.
- Credits are non-transferable and generally non-refundable. Automatic top-up authorizes charges if enabled.

Neither the reviewed API pricing page nor API Terms promises recurring trial credits. Do not tell an exhausted trial user to “wait until tomorrow” without a verified entitlement and reset timestamp.

## When the account's API credits are exhausted

Use this order, with explicit permission before spending or changing account state:

1. **Check website and API entitlements separately on the same account.** Read both API balance fields, then inspect the normal website's current editor access and limits. Historical observation, **2026-09-08**: the same account generated **two neutral couplet edits using website model v2.2 while its API balance was 0**. This supports checking the two surfaces separately; it does not prove unlimited website use, a recurring allowance, or a guarantee that an API subscription funds website edits. Use the website normally, not an undocumented internal API. Automated website access requires the provider's express authorization under the Terms.
2. **Wait only for a verified reset.** If the actual subscription or website UI shows a renewal/reset date and applicable allowance, record it and wait until that time. If no reset is stated, ask support; do not invent one. The public `/pricing` URL returned “Not Found” during this review, so no public website-plan or website-reset guarantee is asserted here.
3. **Reuse already approved material.** Review saved successful candidates, reuse an accepted generation, or make local edits within the user's authorized scope. Do not spend another generation merely to rediscover an existing acceptable result. Reuse does not expand the rights or consent attached to the material.
4. **An existing separately licensed account is only a conditional option.** Consider it only when you are already authorized to operate that account, its license permits this use, and Treblo permits the arrangement. API Terms §7 prohibits sharing/transferring keys or using another customer's keys; §9 prohibits circumventing credit accounting and other controls. Ownership or authorization alone is not a blanket exception. Obtain provider confirmation if unclear. No multi-account workflow was tested, and moving a blocked request to another account is not permitted guidance.
5. **Buy credits or a suitable plan only with budget approval.** Confirm the live price, minimum purchase, renewal terms, and whether the intended editing endpoint is still available before payment. Keep automatic top-up off unless separately authorized. Read back the developer balance after purchase before claiming the credits arrived.
6. **Use a different provider for lawful, authorized material if appropriate.** Verify that it supports source-conditioned editing, the required language, input rights, voice consent, and the budget. Expect different vocals, timing, accompaniment, and transition quality; a substitute is not guaranteed to preserve an exact word edit or the original singer. Switching providers is not a recommendation to evade a moderation or rights restriction.

If none is available, stop generation and report the actual blocker. **Do not use disposable accounts, automated signups, signup farming, key rotation, or account rotation to obtain more trial credits or bypass controls.**

## Moderation and account boundaries

Historical tests encountered a lyric hate-content filter and a duplicate-upload **HTTP 422**. These are distinct from an empty balance. Do not obfuscate rejected lyrics, alter files merely to defeat duplicate detection, or change accounts to evade a refusal. Reuse an existing permitted upload when the normal workflow allows it, ask support about an erroneous rejection, or propose a genuinely compliant revision for user approval. Do not claim the rejected request succeeded because a later neutral edit worked.

The [Terms of Service §§3 and 6](https://treblo.com/tos) prohibit unauthorized automation and accounts created through automated means or false pretenses. The [API Terms §§2 and 9](https://treblo.com/api-terms) authorize compliant public-API automation but prohibit bypassing rate limits, credit accounting, moderation, and other technical controls. They also require rights to inputs and consent for identifiable voices/likenesses. This guide does not authorize transferring another customer's credentials.

## Official source register

All checked **2026-09-08** unless explicitly labeled historical:

- [Developer overview](https://treblo.com/developers): trial offer and entry to account setup.
- [Public signup](https://treblo.com/login?redirectUrl=%2Fdevelopers%2Faccount&mode=signup): authentication options; signup was not submitted during this review.
- [API pricing](https://treblo.com/developers/pricing): current advertised plans, feature costs, and billing-period resets.
- [API documentation](https://treblo.com/developers/docs): balance fields, generation parameters, model status.
- [API Terms](https://treblo.com/api-terms), dated **2026-08-20**: §§7–10 cover keys, credits, restrictions, and availability.
- [Terms of Service](https://treblo.com/tos), dated **2026-08-20**: account eligibility, automation, registration, and content rules.

For unresolved API eligibility, billing, or licensing questions, the API Terms list **api@treblo.com**; the Terms of Service list **support@treblo.com**. These are public provider contacts, not private account details.
