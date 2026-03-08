from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Set


APPROVED_PLUGINS: Set[str] = {
    "adaptive_exit_controller_v1",
    "algo_atr_price_flow_scanner",
    "algo_cash_tactical_rebound_v1",
    "algo_gap_trader_v1",
    "algo_kan_cre",
    "algo_leader_dna_validator_v1",
    "algo_leader_range_play",
    "algo_micro_mr_intraday_v1",
    "algo_micro_vwap_mean_reversion_v1",
    "algo_momo_regime_breakout",
    "algo_overnight_drift_capture_v1",
    "algo_pullback_swing1d",
    "algo_qmr_conformal_swing_v1",
    "algo_rf_monkeys_v1",
    "algo_rs_scanner",
    "algo_silent_strength",
    "algo_tactical_dip_v1",
    "algo_vcp_sniper",
    "alpha_bayesian_inference_v1",
    "alpha_execution_arbiter_v1",
    "alpha_gamma_exposure_v1",
    "alpha_kan_sanity_gate_v1",
    "alpha_market_decoupling",
    "alpha_neural_kelly_scaler_v1",
    "alpha_relative_rank_sieve_v1",
    "alpha_rs_convexity",
    "alpha_vcp_stealth",
    "battle_intel_aggregator_v1",
    "bayes_activation_v1",
    "cash_carry_engine",
    "cava_macro_pack",
    "config_audit_v1",
    "config_consistency_auditor_v1",
    "confirm_then_enter_v1",
    "context_enricher",
    "corp_actions_yahoo",
    "data_ibkr_v1",
    "europe_structural_inefficiency_universe_v1",
    "event_risk_context_v1",
    "exposure_aggregator_v1",
    "FX_EURUSD_SessionLiquidityEngine",
    "feat_shareholder_yield_v1",
    "feat_signal_volatility",
    "gate_decision_audit_v1",
    "ICT_Wyckoff_SessionOrchestrator",
    "infra_signal_audit_v1",
    "market_context_deep",
    "market_doom_gate_alarm",
    "market_health_monitor",
    "market_risk_brief",
    "MEAN_REVERSION_ARBITER",
    "operability_cash_ibkr_v2",
    "options_market_data_bridge_v1",
    "options_overlay_convexity_v1",
    "options_overlay_short_vol_v1",
    "overnight_drift_capture_v1",
    "overnight_intraday_split_v1",
    "plugin_ibkr_usa200_structural_swing",
    "plugin_ohlcv_schema_normalizer_v1",
    "policy_soft_risk_allocator_v1",
    "post_event_reversion_gate_v1",
    "probabilistic_residual_gate_v1",
    "provider_fmp",
    "provider_polygon",
    "provider_premium_bridge_v1",
    "provider_yahoo",
    "ref_data_simple",
    "regime_aware_limits_v1",
    "regime_breadth",
    "regime_ensemble_switcher_v1",
    "regime_entropy",
    "regime_performance_tracker_v1",
    "report_manual_helper",
    "return_decomposition_residual_alpha_v1",
    "risk_correlation_matrix_v1",
    "risk_cash_v1",
    "risk_killswitch_v1",
    "risk_logical_sizing",
    "run_contract_guard",
    "signal_ledger_and_delayed_eval_v1",
    "signal_survival_engine",
    "slippage_estimator_v1",
    "stress_validation_soft_vs_hard_v1",
    "style_premia_long_only",
    "universe_cleaner",
    "universe_dynamic",
    "universe_expander_audit_v1",
    "universe_hardener_v2",
    "universe_prefilter",
    "volatility_regime_engine_v1",
    "vwap_volatility_executor_v1",
    "wait_confirm_translator_v1",
}


DEPRECATED_PLUGINS: Dict[str, str] = {
    "operability_cash_ibkr_v1": "Contains hardcoded limits. Use operability_cash_ibkr_v2.",
}


CONFIG_PLUGIN_ALIASES: Dict[str, str] = {
    "algo_cash_tactical_rebound": "algo_cash_tactical_rebound_v1",
    "gate_decision_audit": "gate_decision_audit_v1",
}


def validate_plugin(plugin_name: str):
    if plugin_name in DEPRECATED_PLUGINS:
        raise RuntimeError(
            f"Plugin '{plugin_name}' is deprecated and blocked. {DEPRECATED_PLUGINS[plugin_name]}"
        )
    if plugin_name not in APPROVED_PLUGINS:
        raise RuntimeError(
            f"Plugin '{plugin_name}' is not approved. "
            "Legacy or non-limits-compliant plugins are blocked."
        )


def validate_plugin_module(module_name: str):
    prefix = "scipia.plugins."
    if not module_name.startswith(prefix):
        return
    plugin_name = module_name[len(prefix) :].split(".", 1)[0]
    if not plugin_name:
        return
    plugins_root = Path("scipia/plugins")
    known_plugins = {p.name for p in plugins_root.iterdir() if p.is_dir()} if plugins_root.exists() else set()
    if plugin_name not in known_plugins and plugin_name not in DEPRECATED_PLUGINS:
        return
    validate_plugin(plugin_name)


def list_deprecated_plugins_found(plugins_root: Path | None = None) -> List[str]:
    root = plugins_root or Path("scipia/plugins")
    found: List[str] = []
    if not root.exists():
        return found
    for plugin_name in sorted(DEPRECATED_PLUGINS):
        if (root / plugin_name).exists():
            found.append(plugin_name)
    return found


def _iter_config_plugin_names(config: dict) -> Iterable[str]:
    for key in config.keys():
        canonical = CONFIG_PLUGIN_ALIASES.get(key, key)
        if canonical in APPROVED_PLUGINS or canonical in DEPRECATED_PLUGINS:
            yield canonical


def find_non_approved_active_plugins(config: dict) -> List[str]:
    active = sorted(set(_iter_config_plugin_names(config)))
    bad: List[str] = []
    for plugin_name in active:
        if plugin_name in DEPRECATED_PLUGINS or plugin_name not in APPROVED_PLUGINS:
            bad.append(plugin_name)
    return bad
