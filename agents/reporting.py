#!/usr/bin/env python3
"""
Reporting Agent
Generates comprehensive reports and analytics
"""

import pandas as pd
import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class ReportingAgent:
    """
    Agent responsible for:
    - Monthly performance reports
    - Trade forensics (why wins/losses)
    - Visual charts and dashboards
    - Performance attribution
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.results_dir = self.base_dir / "backtest_results"
        self.reports_dir = self.base_dir / "reports"
        self.log_file = self.base_dir / "logs" / f"reporting_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.task = self.load_task(task_file) if task_file else None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [REPORTING_AGENT] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def generate_monthly_report(self, include_charts=True):
        """Generate comprehensive month-by-month report"""
        self.log("Generating monthly report...")
        
        # Find all backtest results
        results = []
        for f in self.results_dir.glob("backtest_*.json"):
            with open(f) as file:
                data = json.load(file)
                results.append(data)
        
        if not results:
            self.log("No backtest results found")
            return None
        
        # Combine all monthly data
        all_months = []
        for result in results:
            year = result.get('year')
            for month_num, month_data in result.get('monthly_breakdown', {}).items():
                all_months.append({
                    'year': year,
                    'month': int(month_num),
                    'month_name': month_data['month_name'],
                    'trades': month_data['trades'],
                    'wins': month_data['wins'],
                    'losses': month_data['losses'],
                    'win_rate': month_data['win_rate'],
                    'return_pct': month_data['return_pct']
                })
        
        # Sort by date
        all_months.sort(key=lambda x: (x['year'], x['month']))
        
        # Generate report
        report = {
            'generated': datetime.now().isoformat(),
            'period': f"{all_months[0]['month_name']} {all_months[0]['year']} - {all_months[-1]['month_name']} {all_months[-1]['year']}",
            'summary': {
                'total_months': len(all_months),
                'total_trades': sum(m['trades'] for m in all_months),
                'avg_trades_per_month': sum(m['trades'] for m in all_months) / len(all_months),
                'best_month': max(all_months, key=lambda x: x['return_pct']),
                'worst_month': min(all_months, key=lambda x: x['return_pct']),
            },
            'monthly_data': all_months
        }
        
        # Save report
        report_file = self.reports_dir / f"monthly_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.log("="*70)
        self.log("MONTH-BY-MONTH PERFORMANCE REPORT")
        self.log("="*70)
        self.log(f"Period: {report['period']}")
        self.log(f"Total Months: {report['summary']['total_months']}")
        self.log(f"Total Trades: {report['summary']['total_trades']}")
        self.log(f"Avg Trades/Month: {report['summary']['avg_trades_per_month']:.1f}")
        self.log("")
        
        for month in all_months:
            self.log(f"{month['month_name'][:3]} {month['year']}: {month['trades']:3d} trades | {month['return_pct']:+6.2f}% | WR: {month['win_rate']:5.1f}%")
        
        self.log("")
        best = report['summary']['best_month']
        worst = report['summary']['worst_month']
        self.log(f"Best Month:  {best['month_name']} {best['year']} ({best['return_pct']:+.2f}%)")
        self.log(f"Worst Month: {worst['month_name']} {worst['year']} ({worst['return_pct']:+.2f}%)")
        self.log(f"Report saved: {report_file}")
        self.log("="*70)
        
        return report
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if task_name == "generate_monthly_report":
            include_charts = params.get('include_charts', True)
            result = self.generate_monthly_report(include_charts)
            return result is not None
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = ReportingAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("Reporting Agent ready")

if __name__ == "__main__":
    main()
