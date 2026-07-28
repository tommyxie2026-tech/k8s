from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class WorkflowConfirmationError(PermissionError):
    """Raised when a destructive workflow lacks the required confirmation."""


@dataclass(frozen=True)
class WorkflowSafetyDecision:
    destructive: bool
    required_phrase: str | None


class WorkflowSafetyPolicy:
    """Central policy for destructive workflow confirmation.

    Workflow definitions declare whether an operation is destructive and may
    optionally provide a confirmation phrase. The API and workflow engine must
    use this policy rather than implementing confirmation checks independently.
    """

    DEFAULT_CONFIRM_PHRASE = "CONFIRM"

    def evaluate_definition(self, definition: Mapping[str, Any]) -> WorkflowSafetyDecision:
        destructive = bool(definition.get("destructive", False))
        if not destructive:
            return WorkflowSafetyDecision(destructive=False, required_phrase=None)

        raw_phrase = definition.get("confirm_phrase", self.DEFAULT_CONFIRM_PHRASE)
        phrase = str(raw_phrase).strip()
        if not phrase:
            raise ValueError("destructive workflow definition requires a non-empty confirm_phrase")
        return WorkflowSafetyDecision(destructive=True, required_phrase=phrase)

    def require_confirmation(
        self,
        definition: Mapping[str, Any],
        *,
        confirm: bool,
        confirm_phrase: str,
        workflow_name: str,
    ) -> WorkflowSafetyDecision:
        decision = self.evaluate_definition(definition)
        if not decision.destructive:
            return decision

        assert decision.required_phrase is not None
        if not confirm or confirm_phrase != decision.required_phrase:
            raise WorkflowConfirmationError(
                f"workflow {workflow_name} requires confirm=true and "
                f"confirm_phrase={decision.required_phrase}"
            )
        return decision


workflow_safety_policy = WorkflowSafetyPolicy()
