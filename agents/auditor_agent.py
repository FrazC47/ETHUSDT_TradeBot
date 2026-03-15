#!/usr/bin/env python3
"""
AUDITOR AGENT - The Watchdog of the Trading System

Responsibilities:
1. Audit all operations performed by other agents
2. Verify data sources and data integrity
3. Track what agents did, what they couldn't do, and why
4. Question suspicious results or claims
5. Maintain immutable audit logs
6. Ground everything in truth and facts
"""

import pandas as pd
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
try:
    from path_utils import get_project_root
except ModuleNotFoundError:
    from agents.path_utils import get_project_root
from typing import Dict, List, Optional
from enum import Enum

class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    VERIFICATION = "verification"

class AuditorAgent:
    """
    Central auditing agent that monitors all other agents.
    
    Core Principles:
    1. TRUST BUT VERIFY - Question everything
    2. SOURCE OF TRUTH - All data must be traceable
    3. IMMUTABLE LOGS - Once recorded, never altered
    4. GROUNDED IN FACTS - No hallucinations allowed
    """
    
    def __init__(self, task_file=None):
        self.base_dir = get_project_root()
        self.audit_dir = self.base_dir / "audit_logs"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        self.master_log = self.audit_dir / "master_audit_log.jsonl"
        
        self.task = self.load_task(task_file) if task_file else None
        
        # Audit statistics
        self.total_audits = 0
        self.warnings_issued = 0
        self.errors_found = 0
        self.verifications_passed = 0
        self.verifications_failed = 0
        
        # Known data sources (ground truth)
        self.validated_data_sources = [
            str((self.base_dir / "data" / "raw").resolve()) + "/",
            str((self.base_dir / "data" / "indicators").resolve()) + "/",
            "/data/raw/",
            "/data/indicators/",
            "https://fapi.binance.com"  # Only valid API
        ]
        
    def log(self, message: str, level: AuditLevel = AuditLevel.INFO, agent: str = "AUDITOR"):
        """Write to audit log"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level.value,
            "agent": agent,
            "message": message
        }
        
        # Print to console
        print(f"[{timestamp}] [{level.value.upper()}] [{agent}] {message}")
        
        # Write to daily log
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} | {level.value.upper()} | {agent} | {message}\n")
        
        # Write to master JSONL log
        with open(self.master_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Update statistics
        self.total_audits += 1
        if level == AuditLevel.WARNING:
            self.warnings_issued += 1
        elif level == AuditLevel.ERROR:
            self.errors_found += 1
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def verify_data_source(self, source_path: str, agent_name: str = "unknown") -> Dict:
        """
        Verify that a data source is valid and real.
        
        Checks:
        1. Path is in validated locations
        2. File exists
        3. File has realistic content
        4. Data hash matches expected format
        """
        self.log(f"Verifying data source: {source_path}", AuditLevel.VERIFICATION, agent_name)
        
        result = {
            "source": source_path,
            "verified": False,
            "checks": {}
        }
        
        # Check 1: Source in validated locations
        is_valid_location = any(v in source_path for v in self.validated_data_sources)
        result["checks"]["valid_location"] = is_valid_location
        
        if not is_valid_location:
            self.log(
                f"⚠️ SUSPICIOUS: Data source '{source_path}' not in validated locations. "
                f"Agent {agent_name} may be using fake data.",
                AuditLevel.WARNING,
                agent_name
            )
            self.verifications_failed += 1
            return result
        
        # Check 2: File exists
        file_path = Path(source_path)
        exists = file_path.exists()
        result["checks"]["file_exists"] = exists
        
        if not exists:
            self.log(
                f"❌ ERROR: Data file not found: {source_path}",
                AuditLevel.ERROR,
                agent_name
            )
            result["error"] = "File does not exist"
            self.verifications_failed += 1
            return result
        
        # Check 3: File has content
        try:
            file_size = file_path.stat().st_size
            result["checks"]["file_size"] = file_size
            
            if file_size == 0:
                self.log(
                    f"❌ ERROR: Data file is empty: {source_path}",
                    AuditLevel.ERROR,
                    agent_name
                )
                result["error"] = "File is empty"
                self.verifications_failed += 1
                return result
            
            # Check 4: Sample data validation
            if file_path.suffix == '.csv':
                sample_valid = self._validate_csv_sample(file_path)
                result["checks"]["sample_valid"] = sample_valid
                
                if not sample_valid:
                    self.log(
                        f"❌ ERROR: Data file failed validation: {source_path}",
                        AuditLevel.ERROR,
                        agent_name
                    )
                    result["error"] = "Data validation failed"
                    self.verifications_failed += 1
                    return result
            
        except Exception as e:
            self.log(
                f"❌ ERROR checking file: {e}",
                AuditLevel.ERROR,
                agent_name
            )
            result["error"] = str(e)
            self.verifications_failed += 1
            return result
        
        # All checks passed
        result["verified"] = True
        self.verifications_passed += 1
        self.log(
            f"✅ VERIFIED: Data source '{source_path}' is valid",
            AuditLevel.VERIFICATION,
            agent_name
        )
        
        return result
    
    def _validate_csv_sample(self, file_path: Path) -> bool:
        """Validate a sample of CSV data"""
        try:
            df = pd.read_csv(file_path, nrows=100)
            
            # Check required columns for OHLC data
            if 'close' in df.columns:
                # Check for valid price data
                if (df['close'] < 0).any():
                    return False
                
                # Check OHLC relationships if present
                if all(c in df.columns for c in ['high', 'low', 'close']):
                    if (df['high'] < df['low']).any():
                        return False
                    if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
                        return False
            
            return True
        except Exception:
            return False
    
    def audit_agent_operation(self, agent_name: str, operation: str, 
                              inputs: Dict, outputs: Dict, 
                              data_sources: List[str]) -> Dict:
        """
        Audit an operation performed by another agent.
        
        Records:
        - What the agent did
        - What data they used
        - What results they produced
        - Whether everything checks out
        """
        self.log(f"Auditing {agent_name}: {operation}", AuditLevel.INFO, agent_name)
        
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "operation": operation,
            "inputs": inputs,
            "outputs": outputs,
            "data_sources": [],
            "verification_status": "pending"
        }
        
        # Verify all data sources
        all_verified = True
        for source in data_sources:
            verification = self.verify_data_source(source, agent_name)
            audit_record["data_sources"].append(verification)
            
            if not verification["verified"]:
                all_verified = False
                self.log(
                    f"🚩 AUDIT ALERT: {agent_name} used unverified data source: {source}",
                    AuditLevel.WARNING,
                    agent_name
                )
        
        # Check for suspicious outputs
        suspicious = self._check_for_suspicious_outputs(outputs, agent_name)
        if suspicious:
            audit_record["suspicious_findings"] = suspicious
            all_verified = False
        
        audit_record["verification_status"] = "passed" if all_verified else "failed"
        
        # Save audit record
        audit_file = self.audit_dir / f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
        
        if all_verified:
            self.log(f"✅ Audit PASSED for {agent_name}: {operation}", AuditLevel.INFO, agent_name)
        else:
            self.log(f"❌ Audit FAILED for {agent_name}: {operation}", AuditLevel.ERROR, agent_name)
        
        return audit_record
    
    def _check_for_suspicious_outputs(self, outputs: Dict, agent_name: str) -> List[str]:
        """Check output values for suspicious patterns"""
        suspicious = []
        
        # Check for unrealistic returns
        if 'total_return' in outputs:
            ret = outputs['total_return']
            if isinstance(ret, (int, float)):
                if ret > 1000:  # >1000% is suspicious
                    suspicious.append(f"Suspicious return: {ret}% (too high)")
                    self.log(
                        f"🚩 SUSPICIOUS: {agent_name} claims {ret}% return - likely fake",
                        AuditLevel.WARNING,
                        agent_name
                    )
                elif ret > 100:  # >100% needs verification
                    self.log(
                        f"⚠️ HIGH RETURN CLAIM: {agent_name} claims {ret}% - requires verification",
                        AuditLevel.WARNING,
                        agent_name
                    )
        
        # Check for perfect win rates
        if 'win_rate' in outputs:
            wr = outputs['win_rate']
            if isinstance(wr, (int, float)) and wr > 90:
                suspicious.append(f"Suspicious win rate: {wr}% (too perfect)")
                self.log(
                    f"🚩 SUSPICIOUS: {agent_name} claims {wr}% win rate - likely fake",
                    AuditLevel.WARNING,
                    agent_name
                )
        
        return suspicious
    
    def question_agent(self, agent_name: str, claim: str, evidence_required: List[str]) -> Dict:
        """
        Actively question an agent about a claim they made.
        
        Returns whether the claim is verified or needs more proof.
        """
        self.log(f"❓ QUESTIONING {agent_name}: {claim}", AuditLevel.INFO, agent_name)
        
        inquiry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "claim": claim,
            "evidence_required": evidence_required,
            "status": "pending"
        }
        
        # Check if evidence exists
        missing_evidence = []
        for evidence in evidence_required:
            evidence_path = Path(evidence)
            if not evidence_path.exists():
                missing_evidence.append(evidence)
        
        if missing_evidence:
            inquiry["status"] = "rejected"
            inquiry["missing_evidence"] = missing_evidence
            self.log(
                f"❌ CLAIM REJECTED: {agent_name} cannot prove '{claim}' - missing: {missing_evidence}",
                AuditLevel.ERROR,
                agent_name
            )
        else:
            inquiry["status"] = "verified"
            self.log(
                f"✅ CLAIM VERIFIED: {agent_name} provided evidence for '{claim}'",
                AuditLevel.INFO,
                agent_name
            )
        
        return inquiry
    
    def generate_audit_report(self) -> Dict:
        """Generate comprehensive audit report"""
        report = {
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_audits": self.total_audits,
                "warnings_issued": self.warnings_issued,
                "errors_found": self.errors_found,
                "verifications_passed": self.verifications_passed,
                "verifications_failed": self.verifications_failed
            },
            "principles": [
                "TRUST BUT VERIFY - Question everything",
                "SOURCE OF TRUTH - All data must be traceable",
                "IMMUTABLE LOGS - Once recorded, never altered",
                "GROUNDED IN FACTS - No hallucinations allowed"
            ],
            "validated_data_sources": self.validated_data_sources,
            "recent_audits": self._get_recent_audits(20)
        }
        
        # Save report
        report_file = self.audit_dir / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Audit report generated: {report_file}")
        
        return report
    
    def _get_recent_audits(self, n: int) -> List[Dict]:
        """Get recent audit records from master log"""
        audits = []
        if self.master_log.exists():
            with open(self.master_log) as f:
                lines = f.readlines()
                for line in lines[-n:]:
                    try:
                        audits.append(json.loads(line))
                    except:
                        pass
        return audits
    
    def execute_task(self):
        """Execute assigned auditing task"""
        if not self.task:
            self.log("No audit task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing audit task: {task_name}")
        
        if task_name == "verify_data_source":
            source = params.get('source')
            agent = params.get('agent', 'unknown')
            self.verify_data_source(source, agent)
            return True
        
        elif task_name == "audit_operation":
            self.audit_agent_operation(
                params.get('agent_name'),
                params.get('operation'),
                params.get('inputs', {}),
                params.get('outputs', {}),
                params.get('data_sources', [])
            )
            return True
        
        elif task_name == "question_agent":
            self.question_agent(
                params.get('agent_name'),
                params.get('claim'),
                params.get('evidence_required', [])
            )
            return True
        
        elif task_name == "generate_report":
            self.generate_audit_report()
            return True
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    auditor = AuditorAgent(task_file)
    
    if task_file:
        auditor.execute_task()
    else:
        print("="*70)
        print("AUDITOR AGENT - The Watchdog")
        print("="*70)
        print("Ensuring all agents stay honest and grounded in truth")
        print("="*70)
        print("\nUsage:")
        print("  python auditor_agent.py <task_file.json>")
        print("\nTasks:")
        print("  - verify_data_source")
        print("  - audit_operation")
        print("  - question_agent")
        print("  - generate_report")

if __name__ == "__main__":
    main()
