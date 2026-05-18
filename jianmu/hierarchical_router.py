# SPDX-License-Identifier: AGPL-3.0-only

from typing import List, Optional

from jianmu.ir import ProgramIR
from jianmu.routes import RouteCandidate
from jianmu.semantic_neurons import (
    AdditionNeuron,
    AppendMultipleOperandsNeuron,
    AppendOperandNeuron,
    ArithmeticDomainNeuron,
    ChineseNumberNeuron,
    CodeEditDomainNeuron,
    CodeGenerateDomainNeuron,
    DivisionNeuron,
    ExpressionExtractorNeuron,
    GenerateNewNeuron,
    KeepExistingNeuron,
    MixedExpressionNeuron,
    MultiplicationNeuron,
    NegationDetectorNeuron,
    NeuronResult,
    NoOpDomainNeuron,
    NumberExtractorNeuron,
    QuantityExtractorNeuron,
    ReplaceOperandNeuron,
    RewriteExpressionNeuron,
    SemanticFeatures,
    SubtractionNeuron,
    UnknownDomainNeuron,
    VariableExtractorNeuron,
    has_unsupported_non_addition_expression,
    is_unsupported_english_natural_language,
)


class HierarchicalSemanticRouter:
    """
    Handcrafted neuron scaffold for v0.5.

    Neurons emit local feature votes only. This router aggregates the votes into
    RouteCandidate objects; CandidateExecutor still owns IR construction and
    Sandbox feedback still decides executable correctness.
    """

    def __init__(self):
        self._extraction_neurons = [
            ExpressionExtractorNeuron(),
            NumberExtractorNeuron(),
            ChineseNumberNeuron(),
            NegationDetectorNeuron(),
            QuantityExtractorNeuron(),
            VariableExtractorNeuron(),
        ]
        self._domain_neurons = [
            ArithmeticDomainNeuron(),
            CodeEditDomainNeuron(),
            CodeGenerateDomainNeuron(),
            NoOpDomainNeuron(),
            UnknownDomainNeuron(),
        ]
        self._operation_neurons = [
            AdditionNeuron(),
            SubtractionNeuron(),
            MultiplicationNeuron(),
            DivisionNeuron(),
            MixedExpressionNeuron(),
        ]
        self._edit_intent_neurons = [
            AppendOperandNeuron(),
            AppendMultipleOperandsNeuron(),
            ReplaceOperandNeuron(),
            RewriteExpressionNeuron(),
            KeepExistingNeuron(),
            GenerateNewNeuron(),
        ]

    def analyze(self, user_input: str, previous_ir: Optional[ProgramIR] = None) -> SemanticFeatures:
        features = SemanticFeatures(has_previous_context=previous_ir is not None)
        features.unsupported_language = is_unsupported_english_natural_language(user_input)
        features.unsupported_expression = has_unsupported_non_addition_expression(user_input)
        results: List[NeuronResult] = []

        for neuron in self._extraction_neurons:
            result = neuron.activate(user_input, features)
            self._apply_result(features, result)
            results.append(result)

        for neuron in self._domain_neurons:
            result = neuron.activate(user_input, features)
            self._apply_result(features, result)
            results.append(result)

        for neuron in self._operation_neurons:
            result = neuron.activate(user_input, features)
            self._apply_result(features, result)
            results.append(result)

        for neuron in self._edit_intent_neurons:
            result = neuron.activate(user_input, features)
            self._apply_result(features, result)
            results.append(result)

        features.neuron_results = results
        return features

    def generate_candidates(
        self,
        features: SemanticFeatures,
        previous_ir: Optional[ProgramIR] = None,
    ) -> List[RouteCandidate]:
        prev_count = len(previous_ir.variables) if previous_ir else 0
        if features.unsupported_language:
            return [RouteCandidate(
                route_id="unsupported_language_input",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "unsupported_input",
                    "reason": "english_natural_language_out_of_scope",
                },
                expert_plan=[],
                prior_score=1.0,
                requires_previous_ir=False,
                expected_output_provenance="none",
                semantic_match_score=1.0,
                semantic_features=features.to_dict(),
                rationale="Chinese-first v0.5 rejects English natural-language input",
            )]
        if features.unsupported_expression:
            return [RouteCandidate(
                route_id="unsupported_expression_input",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "unsupported_input",
                    "reason": "non_addition_expression_out_of_scope",
                },
                expert_plan=[],
                prior_score=1.0,
                requires_previous_ir=False,
                expected_output_provenance="none",
                semantic_match_score=1.0,
                semantic_features=features.to_dict(),
                rationale="v0.5 rejects unsupported non-addition expressions",
            )]

        numbers = list(features.extracted_numbers)
        append_value = numbers[-1] if numbers else 1
        replace_value = numbers[-1] if numbers else 1
        quantity = features.quantity or 1
        snapshot = features.to_dict()

        candidates: List[RouteCandidate] = []

        keep_score = features.edit_intent_scores.get("KeepExistingNeuron", 0.0)
        if previous_ir is not None:
            candidates.append(RouteCandidate(
                route_id="no_op_keep_existing",
                source="hierarchical_neuron_tree",
                intent={"action": "keep_existing_program"},
                expert_plan=["IncludeExpert", "PrintfExpert", "MainFunctionExpert", "ConsistencyCheckExpert"],
                prior_score=max(0.05, keep_score),
                requires_previous_ir=True,
                expected_output=f"{sum(v.value for v in previous_ir.variables)}\n",
                expected_output_provenance="previous_ir_noop",
                semantic_match_score=max(0.05, keep_score),
                semantic_features=snapshot,
                rationale="KeepExistingNeuron vote",
            ))

        rewrite_score = features.edit_intent_scores.get("RewriteExpressionNeuron", 0.0)
        if features.extracted_expression and features.expression_values:
            values = list(features.expression_values)
            candidates.append(RouteCandidate(
                route_id="explicit_expression_rewrite",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "rewrite_expression",
                    "values": values,
                    "expression": features.extracted_expression,
                },
                expert_plan=["IncludeExpert", "VariableDefinitionExpert", "SumExpressionExpert",
                             "PrintfExpert", "MainFunctionExpert", "ConsistencyCheckExpert"],
                prior_score=max(0.2, rewrite_score),
                requires_previous_ir=False,
                expected_output=f"{sum(values)}\n",
                expected_output_provenance="explicit_expression",
                semantic_match_score=max(0.2, rewrite_score),
                semantic_features=snapshot,
                rationale="RewriteExpressionNeuron vote",
            ))

        replace_score = features.edit_intent_scores.get("ReplaceOperandNeuron", 0.0)
        if previous_ir is not None:
            candidates.append(RouteCandidate(
                route_id="replace_last_operand",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "replace_last_operand",
                    "target_var_count": prev_count,
                    "new_value": replace_value,
                },
                expert_plan=["IncludeExpert", "ReplaceOperandExpert", "PrintfExpert",
                             "MainFunctionExpert", "ConsistencyCheckExpert"],
                prior_score=max(0.05, replace_score),
                requires_previous_ir=True,
                expected_output=f"{sum(v.value for v in previous_ir.variables[:-1]) + replace_value}\n",
                expected_output_provenance="previous_ir_replace",
                semantic_match_score=max(0.05, replace_score),
                semantic_features=snapshot,
                rationale="ReplaceOperandNeuron vote",
            ))

        append_multi_score = features.edit_intent_scores.get("AppendMultipleOperandsNeuron", 0.0)
        if previous_ir is not None and quantity > 1:
            candidates.append(RouteCandidate(
                route_id="append_multiple_literals_to_existing_sum",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "expand_sum_program",
                    "target_var_count": prev_count + quantity,
                    "new_value": append_value,
                    "append_count": quantity,
                },
                expert_plan=["IncludeExpert", "ExpandSumExpert", "PrintfExpert",
                             "MainFunctionExpert", "ConsistencyCheckExpert"],
                prior_score=max(0.1, append_multi_score),
                requires_previous_ir=True,
                expected_output=f"{sum(v.value for v in previous_ir.variables) + append_value * quantity}\n",
                expected_output_provenance="previous_ir_append",
                semantic_match_score=max(0.1, append_multi_score),
                semantic_features=snapshot,
                rationale="AppendMultipleOperandsNeuron vote",
            ))

        append_score = features.edit_intent_scores.get("AppendOperandNeuron", 0.0)
        append_score = min(append_score, 0.3) if quantity > 1 else append_score
        if previous_ir is not None:
            candidates.append(RouteCandidate(
                route_id="append_literal_to_existing_sum",
                source="hierarchical_neuron_tree",
                intent={
                    "action": "expand_sum_program",
                    "target_var_count": prev_count + 1,
                    "new_value": append_value,
                },
                expert_plan=["IncludeExpert", "ExpandSumExpert", "PrintfExpert",
                             "MainFunctionExpert", "ConsistencyCheckExpert"],
                prior_score=max(0.1, append_score),
                requires_previous_ir=True,
                expected_output=f"{sum(v.value for v in previous_ir.variables) + append_value}\n",
                expected_output_provenance="previous_ir_append",
                semantic_match_score=max(0.1, append_score),
                semantic_features=snapshot,
                rationale="AppendOperandNeuron vote",
            ))

        values = self._generation_values(features)
        generate_score = features.edit_intent_scores.get("GenerateNewNeuron", 0.0)
        candidates.append(RouteCandidate(
            route_id="generate_new_sum_from_text",
            source="hierarchical_neuron_tree",
            intent={
                "action": "generate_sum_program",
                "var_count": len(values),
                "values": values,
            },
            expert_plan=["IncludeExpert", "VariableDefinitionExpert", "SumExpressionExpert",
                         "PrintfExpert", "MainFunctionExpert", "ConsistencyCheckExpert"],
            prior_score=max(0.05, generate_score),
            requires_previous_ir=False,
            expected_output=f"{sum(values)}\n",
            expected_output_provenance="generated_values",
            semantic_match_score=max(0.05, generate_score),
            semantic_features=snapshot,
            rationale="GenerateNewNeuron vote",
        ))

        candidates.sort(key=lambda c: (c.prior_score, c.semantic_match_score), reverse=True)
        return candidates

    def _generation_values(self, features: SemanticFeatures) -> List[int]:
        if features.extracted_expression and features.expression_values:
            return list(features.expression_values)
        numbers = list(features.extracted_numbers)
        if len(numbers) >= 2:
            return numbers
        if features.quantity and features.quantity > 1:
            value = numbers[-1] if numbers else 1
            return [value] * features.quantity
        if numbers:
            value = numbers[-1]
            count = value if value > 1 else 2
            return [value] * count
        return [1, 1]

    def _apply_result(self, features: SemanticFeatures, result: NeuronResult):
        payload = result.features
        if "domain" in payload:
            features.domain_scores[result.neuron_name] = result.score
        if "operation" in payload:
            features.operation_scores[result.neuron_name] = result.score
        if "edit_intent" in payload:
            features.edit_intent_scores[result.neuron_name] = result.score
        if "numbers" in payload:
            features.extracted_numbers.extend(payload["numbers"])
        if "expression" in payload:
            features.extracted_expression = payload["expression"]
        if "expression_values" in payload:
            features.expression_values = payload["expression_values"]
        if "quantity" in payload and payload["quantity"] is not None:
            features.quantity = payload["quantity"]
        if "negated" in payload:
            features.negated = bool(payload["negated"])
        if "variable_focus" in payload:
            features.variable_focus = payload["variable_focus"]
