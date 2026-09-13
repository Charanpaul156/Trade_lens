import re
import math
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any

from app.schemas.research import (
    DefinedExperimentSpec,
    BacktestResult,
    BacktestMetrics,
    SimulatedTrade,
    EquityPoint,
)


class BacktestEngine:
    """
    Deterministic, zero-lookahead research backtesting prototype.
    Internal separation of concerns:
    1. Data generation (deterministic synthetic reference series)
    2. Signal evaluation (candle t close without future peeking)
    3. Order execution (candle t+1 open with explicit slippage)
    4. Position management (conservative same-bar target+stop resolution)
    5. Metrics calculation (robust edge cases: 0 trades, 1 trade, all wins/losses, no NaN)
    """

    SIMULATION_DISCLAIMER = (
        "Deterministic synthetic reference data. Results are illustrative and do not "
        "represent real market performance or live execution."
    )

    EXECUTION_TIMING_CONVENTION = (
        "Signals are strictly evaluated on candle t close. Orders are executed on candle t+1 open "
        "with explicit slippage friction applied on entry and exit. Same-bar profit-target and stop-loss "
        "collisions conservatively assume stop-loss execution first."
    )

    # -------------------------------------------------------------------------
    # 1. Cost & Parameter Parsing Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def parse_slippage_rate(cls, cost_assumptions: str) -> float:
        """
        Parses slippage/friction rate per side.
        Strict parsing: rejects unsupported formats with ValueError instead of guessing.
        """
        clean = cost_assumptions.strip().lower()

        # Zero fees formats
        if any(z in clean for z in ["zero fees", "zero", "idealized", "0%", "0.0%"]):
            return 0.0

        # Pattern: "X.XX% slippage per side" or "X.XX% per side"
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", clean)
        if match:
            pct_val = float(match.group(1))
            return pct_val / 100.0

        raise ValueError(
            f"Unsupported cost assumptions format '{cost_assumptions}'. "
            "Supported formats include '0.05% slippage per side' or 'Zero fees (idealized)'."
        )

    @classmethod
    def parse_entry_threshold(cls, entry_condition: str) -> float:
        """
        Extracts entry percentage threshold (e.g. 1.0% drop).
        Defaults to 0.01 (1%) if standard dip logic is described.
        """
        clean = entry_condition.strip().lower()
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", clean)
        if match:
            return float(match.group(1)) / 100.0
        return 0.01

    @classmethod
    def parse_holding_bars(cls, holding_period: Optional[str]) -> Optional[int]:
        """
        Extracts integer holding period in bars.
        """
        if not holding_period:
            return None
        clean = holding_period.strip().lower()
        match = re.search(r"(\d+)", clean)
        if match:
            return int(match.group(1))
        return 5

    @classmethod
    def parse_exit_targets(cls, exit_condition: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Extracts (profit_target_pct, stop_loss_pct) from exit condition string.
        """
        if not exit_condition:
            return None, None
        clean = exit_condition.strip().lower()

        target_pct = None
        stop_pct = None

        # Look for target / profit: e.g. "2% target"
        target_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:target|profit|take\s*profit)", clean)
        if target_match:
            target_pct = float(target_match.group(1)) / 100.0

        # Look for stop / loss: e.g. "1% stop loss"
        stop_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:stop|loss|stop\s*loss)", clean)
        if stop_match:
            stop_pct = float(stop_match.group(1)) / 100.0

        # Fallback: if two percentages are specified ("2% target or 1% stop")
        if target_pct is None and stop_pct is None:
            pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", clean)
            if len(pcts) >= 2:
                target_pct = float(pcts[0]) / 100.0
                stop_pct = float(pcts[1]) / 100.0
            elif len(pcts) == 1:
                target_pct = float(pcts[0]) / 100.0

        return target_pct, stop_pct

    # -------------------------------------------------------------------------
    # 2. Data Generation (Deterministic Synthetic Reference Data)
    # -------------------------------------------------------------------------

    @classmethod
    def generate_reference_data(
        cls,
        instrument: str,
        seed: int,
        num_bars: int = 500,
        start_date: str = "2020-01-01",
    ) -> List[Dict[str, Any]]:
        """
        Generates deterministic daily OHLCV bars using a seeded pseudo-random sequence.
        100% reproducible for identical seeds.
        """
        # Linear Congruential Generator (LCG) for pure-Python deterministic pseudo-random numbers
        state = seed

        def lcg_random() -> float:
            nonlocal state
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            return state / float(0x7FFFFFFF)

        def lcg_gauss() -> float:
            # Box-Muller transform
            u1 = max(1e-7, lcg_random())
            u2 = lcg_random()
            return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

        base_price = 10000.0 if "nifty" in instrument.lower() else (400.0 if "spy" in instrument.lower() else 150.0)
        curr_price = base_price
        dt = datetime.strptime(start_date, "%Y-%m-%d")

        bars: List[Dict[str, Any]] = []

        for i in range(num_bars):
            # Advance to next business day
            dt += timedelta(days=1)
            while dt.weekday() >= 5:  # Skip Saturday (5) and Sunday (6)
                dt += timedelta(days=1)

            # Daily return with drift and volatility
            daily_vol = 0.012  # ~1.2% daily stdev (~19% annual)
            ret = (0.0003 + daily_vol * lcg_gauss())  # Slight positive equity drift
            prev_close = curr_price
            open_price = prev_close * (1.0 + 0.002 * lcg_gauss())
            close_price = prev_close * (1.0 + ret)

            high_price = max(open_price, close_price) * (1.0 + abs(0.005 * lcg_gauss()))
            low_price = min(open_price, close_price) * (1.0 - abs(0.005 * lcg_gauss()))
            curr_price = close_price

            # Synthetic volatility regime (VIX-like proxy between 12 and 32)
            vix_proxy = 18.0 + 6.0 * math.sin(i / 20.0) + 4.0 * lcg_gauss()

            bars.append({
                "bar_index": i,
                "date": dt.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "vix": round(max(10.0, vix_proxy), 2),
            })

        return bars

    # -------------------------------------------------------------------------
    # 3. Signal Evaluation (Strict Candle t Close, No Look-Ahead)
    # -------------------------------------------------------------------------

    @classmethod
    def evaluate_signal_at_t(
        cls,
        bars: List[Dict[str, Any]],
        t: int,
        drop_threshold: float,
        has_vix_filter: bool,
    ) -> bool:
        """
        Evaluates entry rule using ONLY data available up to Candle t close.
        Never references candle t+1 or any future bars.
        """
        if t <= 0:
            return False

        bar_t = bars[t]
        bar_prev = bars[t - 1]

        # Calculate percentage fall from previous close to current close
        prev_close = bar_prev["close"]
        curr_close = bar_t["close"]
        drop_pct = (prev_close - curr_close) / prev_close

        if drop_pct < drop_threshold:
            return False

        # Regime filter check if specified (e.g. India VIX > 20)
        if has_vix_filter and bar_t["vix"] <= 20.0:
            return False

        return True

    # -------------------------------------------------------------------------
    # 4. Order Execution & Position Management
    # -------------------------------------------------------------------------

    @classmethod
    def simulate_trades(
        cls,
        bars: List[Dict[str, Any]],
        drop_threshold: float,
        has_vix_filter: bool,
        holding_bars: Optional[int],
        target_pct: Optional[float],
        stop_pct: Optional[float],
        slippage_rate: float,
    ) -> List[SimulatedTrade]:
        """
        Simulates sequential trade execution:
        - Signal fires at t Close.
        - Entry executed at t+1 Open with slippage.
        - Conservative same-bar resolution: if both target and stop are triggered on candle k,
          assumes STOP_LOSS occurs first.
        - Single active trade at a time.
        """
        trades: List[SimulatedTrade] = []
        trade_counter = 1
        i = 1
        num_bars = len(bars)

        while i < num_bars - 1:
            # Check signal at bar t = i
            signal_fired = cls.evaluate_signal_at_t(
                bars=bars,
                t=i,
                drop_threshold=drop_threshold,
                has_vix_filter=has_vix_filter,
            )

            if not signal_fired:
                i += 1
                continue

            # Signal fired at candle t = i.
            # ENTRY EXECUTES ON CANDLE t+1 OPEN:
            entry_bar_idx = i + 1
            if entry_bar_idx >= num_bars:
                break

            entry_bar = bars[entry_bar_idx]
            raw_entry_price = entry_bar["open"]
            # Apply entry slippage
            effective_entry_price = round(raw_entry_price * (1.0 + slippage_rate), 2)

            target_price = round(effective_entry_price * (1.0 + target_pct), 2) if target_pct else None
            stop_price = round(effective_entry_price * (1.0 - stop_pct), 2) if stop_pct else None

            # Maximum holding duration horizon
            max_horizon = holding_bars if holding_bars is not None else 20
            exit_bar_idx = min(entry_bar_idx + max_horizon, num_bars - 1)
            exit_reason = "HOLDING_PERIOD_EXPIRY"
            raw_exit_price = bars[exit_bar_idx]["open"]

            # Step forward bar-by-bar through holding window to evaluate target / stop
            curr_bar_idx = entry_bar_idx
            while curr_bar_idx <= exit_bar_idx:
                k_bar = bars[curr_bar_idx]

                hit_stop = stop_price is not None and k_bar["low"] <= stop_price
                hit_target = target_price is not None and k_bar["high"] >= target_price

                if hit_stop and hit_target:
                    # SAME-BAR COLLISION: Conservative convention -> Assume STOP_LOSS first
                    exit_bar_idx = curr_bar_idx
                    exit_reason = "STOP_LOSS"
                    raw_exit_price = stop_price
                    break
                elif hit_stop:
                    exit_bar_idx = curr_bar_idx
                    exit_reason = "STOP_LOSS"
                    raw_exit_price = stop_price
                    break
                elif hit_target:
                    exit_bar_idx = curr_bar_idx
                    exit_reason = "PROFIT_TARGET"
                    raw_exit_price = target_price
                    break

                if curr_bar_idx == exit_bar_idx:
                    # Reached holding period expiration
                    raw_exit_price = k_bar["open"] if curr_bar_idx > entry_bar_idx else k_bar["close"]
                    exit_reason = "HOLDING_PERIOD_EXPIRY"
                    break

                curr_bar_idx += 1

            # Apply exit slippage
            effective_exit_price = round(raw_exit_price * (1.0 - slippage_rate), 2)

            gross_pnl_pct = round((raw_exit_price - raw_entry_price) / raw_entry_price, 4)
            net_pnl_pct = round((effective_exit_price - effective_entry_price) / effective_entry_price, 4)
            friction_paid_pct = round(gross_pnl_pct - net_pnl_pct, 4)
            actual_holding_bars = exit_bar_idx - entry_bar_idx

            trade = SimulatedTrade(
                trade_id=trade_counter,
                entry_bar_index=entry_bar_idx,
                entry_date=entry_bar["date"],
                entry_price=effective_entry_price,
                exit_bar_index=exit_bar_idx,
                exit_date=bars[exit_bar_idx]["date"],
                exit_price=effective_exit_price,
                exit_reason=exit_reason,
                gross_pnl_pct=gross_pnl_pct,
                net_pnl_pct=net_pnl_pct,
                friction_paid_pct=friction_paid_pct,
                holding_bars=max(1, actual_holding_bars),
                is_win=net_pnl_pct > 0.0,
            )
            trades.append(trade)
            trade_counter += 1

            # Advance outer index past this completed trade
            i = max(i + 1, exit_bar_idx + 1)

        return trades

    # -------------------------------------------------------------------------
    # 5. Metrics & Equity Curve Calculation (Zero NaN, Robust Edge Cases)
    # -------------------------------------------------------------------------

    @classmethod
    def calculate_equity_and_metrics(
        cls,
        bars: List[Dict[str, Any]],
        trades: List[SimulatedTrade],
        initial_capital: float,
    ) -> Tuple[List[EquityPoint], BacktestMetrics, float]:
        """
        Builds running equity curve and computes summary risk/return metrics.
        Guaranteed never to return NaN, null divisions, or Infinity.
        """
        equity_curve: List[EquityPoint] = []
        running_equity = float(initial_capital)
        peak_equity = float(initial_capital)
        max_drawdown_pct = 0.0

        # Map trade exits by date for equity updates
        trades_by_exit_date = {t.exit_date: t for t in trades}
        trade_open_windows = set()
        for t in trades:
            for b in range(t.entry_bar_index, t.exit_bar_index + 1):
                trade_open_windows.add(b)

        for bar in bars:
            b_idx = bar["bar_index"]
            b_date = bar["date"]

            if b_date in trades_by_exit_date:
                t = trades_by_exit_date[b_date]
                running_equity = running_equity * (1.0 + t.net_pnl_pct)

            if running_equity > peak_equity:
                peak_equity = running_equity

            dd = 0.0
            if peak_equity > 0:
                dd = (peak_equity - running_equity) / peak_equity
            if dd > max_drawdown_pct:
                max_drawdown_pct = dd

            equity_curve.append(
                EquityPoint(
                    date=b_date,
                    equity=round(running_equity, 2),
                    drawdown_pct=round(dd * 100.0, 2),
                    in_trade=(b_idx in trade_open_windows),
                )
            )

        # Metrics computation
        total_trades = len(trades)
        if total_trades == 0:
            metrics = BacktestMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                net_return_pct=0.0,
                gross_return_pct=0.0,
                friction_drag_pct=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                avg_trade_return_pct=0.0,
                avg_holding_bars=0.0,
                sharpe_ratio=None,
            )
            return equity_curve, metrics, initial_capital

        winning_trades = [t for t in trades if t.is_win]
        losing_trades = [t for t in trades if not t.is_win]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate_pct = round((win_count / total_trades) * 100.0, 2)
        net_returns = [t.net_pnl_pct for t in trades]

        # Calculate compounded gross equity to compare against compounded net equity
        running_gross_equity = initial_capital
        for t in trades:
            running_gross_equity = running_gross_equity * (1.0 + t.gross_pnl_pct)

        gross_return_pct = round(((running_gross_equity - initial_capital) / initial_capital) * 100.0, 2)
        net_return_pct = round(((running_equity - initial_capital) / initial_capital) * 100.0, 2)
        friction_drag_pct = round(gross_return_pct - net_return_pct, 2)

        # Profit factor = Gross gains / abs(Gross losses)
        gross_gains = sum(t.net_pnl_pct for t in winning_trades)
        gross_losses = abs(sum(t.net_pnl_pct for t in losing_trades))

        if gross_losses > 0:
            profit_factor = round(gross_gains / gross_losses, 2)
        elif gross_gains > 0:
            profit_factor = 99.99  # All winning trades
        else:
            profit_factor = 0.0

        avg_trade_return_pct = round((sum(net_returns) / total_trades) * 100.0, 2)
        avg_holding = round(sum(t.holding_bars for t in trades) / total_trades, 1)

        # Sharpe ratio calculation on trade returns
        sharpe: Optional[float] = None
        if total_trades >= 2:
            mean_ret = sum(net_returns) / total_trades
            variance = sum((r - mean_ret) ** 2 for r in net_returns) / (total_trades - 1)
            stdev = math.sqrt(variance)
            if stdev > 1e-6:
                # Annualized proxy assuming ~250 trading days
                annualized_factor = math.sqrt(250.0 / max(1.0, avg_holding))
                sharpe = round((mean_ret / stdev) * annualized_factor, 2)

        metrics = BacktestMetrics(
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate_pct=win_rate_pct,
            net_return_pct=net_return_pct,
            gross_return_pct=gross_return_pct,
            friction_drag_pct=friction_drag_pct,
            profit_factor=profit_factor,
            max_drawdown_pct=round(max_drawdown_pct * 100.0, 2),
            avg_trade_return_pct=avg_trade_return_pct,
            avg_holding_bars=avg_holding,
            sharpe_ratio=sharpe,
        )

        return equity_curve, metrics, round(running_equity, 2)

    # -------------------------------------------------------------------------
    # 6. Primary Entry Point
    # -------------------------------------------------------------------------

    @classmethod
    def run(
        cls,
        spec: DefinedExperimentSpec,
        initial_capital: float = 100000.0,
    ) -> BacktestResult:
        """
        Executes a complete backtest simulation for a locked DefinedExperimentSpec.
        """
        # 1. Deterministic seed from experiment content
        spec_content = (
            f"{spec.market_context.instrument}|{spec.market_context.timeframe}|"
            f"{spec.signal_rules.entry_condition}|{spec.position_rules.exit_condition}|"
            f"{spec.position_rules.holding_period}|{spec.backtest_bounds.test_period}|"
            f"{spec.backtest_bounds.cost_assumptions}"
        )
        spec_hash = hashlib.sha256(spec_content.encode("utf-8")).hexdigest()
        experiment_id = f"EXP-{spec_hash[:8].upper()}"
        seed = int(spec_hash[:8], 16)

        # 2. Parse parameters strictly
        slippage_rate = cls.parse_slippage_rate(spec.backtest_bounds.cost_assumptions)
        drop_threshold = cls.parse_entry_threshold(spec.signal_rules.entry_condition)
        holding_bars = cls.parse_holding_bars(spec.position_rules.holding_period)
        target_pct, stop_pct = cls.parse_exit_targets(spec.position_rules.exit_condition)

        has_vix_filter = any("vix" in f.lower() or "volatility" in f.lower() for f in spec.signal_rules.filters)

        # 3. Generate deterministic reference data
        bars = cls.generate_reference_data(
            instrument=spec.market_context.instrument,
            seed=seed,
            num_bars=500,
        )

        # 4. Simulate trades (zero look-ahead)
        trades = cls.simulate_trades(
            bars=bars,
            drop_threshold=drop_threshold,
            has_vix_filter=has_vix_filter,
            holding_bars=holding_bars,
            target_pct=target_pct,
            stop_pct=stop_pct,
            slippage_rate=slippage_rate,
        )

        # 5. Calculate equity curve & metrics
        equity_curve, metrics, final_equity = cls.calculate_equity_and_metrics(
            bars=bars,
            trades=trades,
            initial_capital=initial_capital,
        )

        return BacktestResult(
            experiment_id=experiment_id,
            instrument=spec.market_context.instrument,
            timeframe=spec.market_context.timeframe,
            test_period=spec.backtest_bounds.test_period,
            initial_capital=initial_capital,
            final_equity=final_equity,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
            execution_timing_convention=cls.EXECUTION_TIMING_CONVENTION,
            simulation_disclaimer=cls.SIMULATION_DISCLAIMER,
            reproducible_seed=seed,
        )
