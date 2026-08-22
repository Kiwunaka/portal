"use client";

import { useMemo, useState } from "react";
import { CircleOff, Play, RefreshCw, RotateCcw, ShieldCheck } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Button, Card, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import type { NodeObservability } from "@/lib/admin-api/nodes";

type NodeActionDefinition = {
  label: string;
  hint: string;
  request: ActionIntentRequest;
  tone: "primary" | "secondary" | "danger";
  icon: typeof Play;
  disabled?: boolean;
};

function actionRequest(
  code: string,
  command: "drain" | "undrain" | "enable" | "disable" | "resync",
  payload: Record<string, unknown>,
): ActionIntentRequest {
  return {
    action: `node.${command}`,
    target: { type: "node", id: code },
    payload,
    endpoint: "",
    workspace: "network",
  };
}

export function NodeActions({
  data,
  onRefreshNode,
}: {
  data: NodeObservability;
  onRefreshNode: () => void;
}) {
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const code = data.node.code.trim().toLowerCase();
  const mappedUsers = data.lifecycle.mapped_users;

  const actions = useMemo<NodeActionDefinition[]>(() => {
    if (!data.lifecycle.enabled) {
      return [
        {
          label: "Включить ноду",
          hint: "Вернуть ноду в рабочий контур и разрешить новые размещения.",
          request: actionRequest(code, "enable", { force: false }),
          tone: "primary",
          icon: Play,
        },
        ...(typeof mappedUsers === "number" && mappedUsers > 0 ? [{
          label: "Перенести клиентов",
          hint: "Перенести зафиксированную сервером выборку с отключённой ноды.",
          request: actionRequest(code, "resync", { limit: 100, dry_run: false }),
          tone: "secondary" as const,
          icon: RefreshCw,
        }] : []),
      ];
    }

    if (data.lifecycle.is_draining || !data.lifecycle.accepting_new_clients) {
      if (typeof mappedUsers === "number" && mappedUsers > 0) {
        return [
          {
            label: "Перенести клиентов",
            hint: "Перенести точную выборку привязок из серверного предпросмотра.",
            request: actionRequest(code, "resync", { limit: 100, dry_run: false }),
            tone: "primary",
            icon: RefreshCw,
          },
          {
            label: "Вернуть в контур",
            hint: "Снова разрешить новые размещения на этой ноде.",
            request: actionRequest(code, "undrain", { force: false }),
            tone: "secondary",
            icon: RotateCcw,
          },
        ];
      }
      return [
        {
          label: "Вернуть в контур",
          hint: "Снова разрешить новые размещения на этой ноде.",
          request: actionRequest(code, "undrain", { force: false }),
          tone: "secondary",
          icon: RotateCcw,
        },
        {
          label: "Отключить ноду",
          hint: "Отключить пустую ноду после ввода её точного кода.",
          request: actionRequest(code, "disable", { force: false }),
          tone: "danger",
          icon: CircleOff,
          disabled: mappedUsers === null,
        },
      ];
    }

    return [
      {
        label: "Вывести из контура",
        hint: "Остановить новые размещения; текущие привязки останутся на ноде.",
        request: actionRequest(code, "drain", { force: false }),
        tone: "secondary",
        icon: ShieldCheck,
      },
      {
        label: "Отключить ноду",
        hint: typeof mappedUsers === "number" && mappedUsers > 0
          ? "Принудительное отключение: серверный предпросмотр покажет число привязок и потребует код ноды."
          : "Полностью отключить ноду после ввода её точного кода.",
        request: actionRequest(code, "disable", { force: typeof mappedUsers === "number" && mappedUsers > 0 }),
        tone: "danger",
        icon: CircleOff,
        disabled: mappedUsers === null,
      },
    ];
  }, [code, data.lifecycle.accepting_new_clients, data.lifecycle.enabled, data.lifecycle.is_draining, mappedUsers]);

  function openAction(nextRequest: ActionIntentRequest) {
    setRequest(nextRequest);
    setDialogOpen(true);
  }

  return (
    <>
      <Card className="min-h-0">
        <SectionTitle
          title="Действия ноды"
          description="Для каждой команды сервер сначала готовит предпросмотр на 10 минут. Команда выполняется один раз и всегда оставляет ID аудита."
        />
        <div className="grid gap-2 sm:grid-cols-2">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <div key={action.request.action} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
                <Button
                  tone={action.tone}
                  disabled={action.disabled}
                  className="w-full sm:w-auto"
                  onClick={() => openAction(action.request)}
                >
                  <Icon size={15} /> {action.label}
                </Button>
                <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">
                  {action.disabled ? "Действие заблокировано: сервер не вернул число привязок." : action.hint}
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(nextOpen) => {
          setDialogOpen(nextOpen);
          if (!nextOpen) setRequest(null);
        }}
        onKnownOutcome={onRefreshNode}
        onCheckState={onRefreshNode}
      />
    </>
  );
}
