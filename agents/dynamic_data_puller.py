#!/usr/bin/env python3
"""
ETHUSDT Dynamic Data Puller
Switches between 5m (normal) and 1m (setup active) based on agent state.
Saves API calls while providing granular data when needed.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests

try:
    from path_utils import get_project_root
except ModuleNotFoundError:
    from agents.path_utils import get_project_root

BASE_DIR = get_project_root()

# Configuration
DYNAMIC_CONFIG = {
    'symbol': 'ETHUSDT',
    'normal_interval': '5m',
    'granular_interval': '1m',

    # Paths
    'state_file': str(BASE_DIR / 'state' / 'agent_state.json'),
    'data_dir': str(BASE_DIR / 'data'),
    'log_file': str(BASE_DIR / 'logs' / 'dynamic_puller.log'),

    # Timing
    'setup_max_age_minutes': 30,
}

CSV_HEADER = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
    'taker_buy_quote_volume', 'ignore'
]


class DynamicDataPuller:
    """Dynamically switches data pull frequency based on setup status."""

    def __init__(self):
        self.config = DYNAMIC_CONFIG
        self.setup_logging()

    def setup_logging(self):
        self.log_file = Path(self.config['log_file'])
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_line)
        print(log_line.strip())

    def load_agent_state(self) -> Dict:
        state_file = Path(self.config['state_file'])
        if state_file.exists():
            with open(state_file, 'r') as f:
                return json.load(f)
        return {'active_setup': None, 'last_setup_time': None}

    def is_setup_active(self, state: Dict) -> bool:
        if state.get('granular_mode_active'):
            activated_at = state.get('granular_mode_activated_at')
            if activated_at:
                activated_dt = datetime.fromisoformat(activated_at)
                age_minutes = (datetime.now() - activated_dt).total_seconds() / 60
                return age_minutes < self.config['setup_max_age_minutes']

        if state.get('active_setup'):
            setup_time = state['active_setup'].get('timestamp')
            if setup_time:
                setup_dt = datetime.fromisoformat(setup_time)
                age_minutes = (datetime.now() - setup_dt).total_seconds() / 60
                return age_minutes < self.config['setup_max_age_minutes']

        return False

    def _fetch_klines(self, interval: str) -> List[List]:
        params = {'symbol': self.config['symbol'], 'interval': interval, 'limit': 100}
        response = requests.get("https://api.binance.com/api/v3/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError(f"Unexpected kline response: {data}")
        return data

    def _load_existing_rows(self, output_file: Path) -> Dict[str, List[str]]:
        rows_by_open_time = {}
        if not output_file.exists():
            return rows_by_open_time

        with open(output_file, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != CSV_HEADER:
                self.log("⚠️ Existing CSV header mismatch; rewriting with canonical header")
                return rows_by_open_time
            for row in reader:
                if row:
                    rows_by_open_time[row[0]] = row
        return rows_by_open_time

    def _write_rows(self, output_file: Path, rows_by_open_time: Dict[str, List[str]]):
        sorted_rows = [rows_by_open_time[k] for k in sorted(rows_by_open_time.keys(), key=int)]
        tmp_file = output_file.with_suffix('.tmp')
        with open(tmp_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(sorted_rows)
        tmp_file.replace(output_file)

    def pull_data(self, interval: str):
        self.log(f"Pulling {interval} data for {self.config['symbol']}")

        output_file = Path(self.config['data_dir']) / f"{interval}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            klines = self._fetch_klines(interval)
            rows_by_open_time = self._load_existing_rows(output_file)
            before_count = len(rows_by_open_time)

            for candle in klines:
                row = [str(v) for v in candle[:12]]
                rows_by_open_time[row[0]] = row

            self._write_rows(output_file, rows_by_open_time)
            added = len(rows_by_open_time) - before_count
            self.log(f"✅ Successfully synchronized {len(klines)} {interval} candles ({added:+d} unique rows)")
            return True

        except Exception as e:
            self.log(f"❌ Error pulling {interval} data: {e}")
            return False

    def run(self):
        self.log("=" * 60)
        self.log("DYNAMIC DATA PULLER STARTING")
        self.log("=" * 60)

        state = self.load_agent_state()

        if self.is_setup_active(state):
            mode = 'GRANULAR'
            interval = self.config['granular_interval']
        else:
            mode = 'NORMAL'
            interval = self.config['normal_interval']

        self.log(f"Mode: {mode} (pulling {interval} data)")
        success = self.pull_data(interval)

        self.log("=" * 60)
        if success:
            self.log(f"✅ {mode} mode complete - {interval} data updated")
        else:
            self.log(f"⚠️ {mode} mode failed - will retry next cycle")
        self.log("=" * 60)


if __name__ == '__main__':
    puller = DynamicDataPuller()
    puller.run()
