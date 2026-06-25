/**
 * Supabase Realtime hook — live inventory updates.
 *
 * Subscribes to PostgreSQL changes on inventory_items and alerts
 * tables via Supabase Realtime (listens to Postgres WAL replication).
 *
 * When a backend transaction commits (issue/restock/transfer),
 * Supabase broadcasts the change and this hook invalidates the
 * relevant React Query cache entries — triggering a refetch.
 *
 * Prerequisites in Supabase dashboard:
 *   Database → Replication → enable replication for:
 *     - inventory_items (INSERT, UPDATE)
 *     - alerts (INSERT, UPDATE)
 */
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

export function useRealtimeInventory() {
  const qc = useQueryClient();

  useEffect(() => {
    const channel = supabase
      .channel("inventory-realtime")
      // Inventory item changes
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "inventory_items",
        },
        (payload) => {
          // Invalidate the affected item and the list
          const itemId = (payload.new as any)?.id ?? (payload.old as any)?.id;
          qc.invalidateQueries({ queryKey: ["inventory", "items"] });
          if (itemId) {
            qc.invalidateQueries({ queryKey: ["inventory", "item", itemId] });
          }
        }
      )
      // New alerts
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "alerts",
        },
        () => {
          qc.invalidateQueries({ queryKey: ["alerts"] });
        }
      )
      // Alert status updates (ack / resolve)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "alerts",
        },
        () => {
          qc.invalidateQueries({ queryKey: ["alerts"] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [qc]);
}
