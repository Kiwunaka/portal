# Migration to Multi-Node

There is no vendor "migration" for 3x-ui. We migrate *our* user database and recreate clients on each node.

## How Users Get New Nodes

New nodes get existing users like this:

1. `portal.db` stays the source of truth (users, uuid, sub_token, is_active, expiry).
2. For each new node, we call the node panel API and create (or update) a client in that node's inbound:
   - `tgId = user.tg_id`
   - `id (uuid) = user.uuid` (same uuid on all nodes)
   - `subId = user.sub_token` (or tg_id fallback)
   - `enable = user.is_active`
3. Subscription endpoint starts returning multiple locations, so the user can switch location inside their client app.

From the user's perspective: they just refresh/update the subscription once to see new locations.

## Procedure

1. Backup control-plane DB (`portal.db`).
2. Bootstrap node A (fresh server) and configure inbound (Reality).
3. Add node A to `nodes`:
   - `python scripts/add_node.py ...`
4. Run sync:
   - `python scripts/migrate_to_nodes.py --node <code>`
5. Repeat for other nodes.
6. Verify:
   - Subscription returns multiple countries.
   - Selected users can connect via at least 2 nodes.
