#!/usr/bin/env python3
"""
SMB Connectivity Diagnostics Tool

This script performs comprehensive SMB connectivity testing to identify
specific issues based on the root cause analysis.
"""

import socket
import subprocess
import sys
import time
import argparse
from typing import Dict, List, Tuple, Optional
import json

class SMBDiagnostics:
    def __init__(self, target_ip: str, username: str = None, password: str = None):
        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.results = {}
        
    def test_port_connectivity(self) -> bool:
        """Test if port 445 is reachable."""
        print("🔍 Testing port 445 connectivity...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target_ip, 445))
            sock.close()
            
            if result == 0:
                print("✅ Port 445 is reachable")
                self.results['port_445'] = True
                return True
            else:
                print("❌ Port 445 is not reachable")
                self.results['port_445'] = False
                return False
        except Exception as e:
            print(f"❌ Port 445 test failed: {e}")
            self.results['port_445'] = False
            return False
    
    def test_smb_versions(self) -> Dict[str, bool]:
        """Test SMB version compatibility."""
        print("\n🔄 Testing SMB version compatibility...")
        versions = {
            'SMB1': '--option=client min protocol=NT1',
            'SMB2': '--option=client min protocol=SMB2', 
            'SMB3': '--option=client min protocol=SMB3'
        }
        
        results = {}
        for version, option in versions.items():
            print(f"  Testing {version}...")
            try:
                cmd = ['smbclient', '-L', f'//{self.target_ip}', '-U', '', '-N', option]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"    ✅ {version} is supported")
                    results[version] = True
                else:
                    print(f"    ❌ {version} not supported")
                    results[version] = False
            except Exception as e:
                print(f"    ❌ {version} test failed: {e}")
                results[version] = False
        
        self.results['smb_versions'] = results
        return results
    
    def test_authentication_methods(self) -> Dict[str, bool]:
        """Test different authentication methods."""
        print("\n🔐 Testing authentication methods...")
        
        methods = [
            ('anonymous', '', ''),
            ('guest', 'guest', ''),
            ('null_session', '', ''),
        ]
        
        if self.username:
            methods.append(('provided_credentials', self.username, self.password or ''))
        
        results = {}
        for method_name, user, password in methods:
            print(f"  Testing {method_name}...")
            try:
                if password:
                    cmd = ['smbclient', '-L', f'//{self.target_ip}', '-U', user, '-p', password]
                else:
                    cmd = ['smbclient', '-L', f'//{self.target_ip}', '-U', user, '-N']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'Sharename' in result.stdout:
                    print(f"    ✅ {method_name} successful")
                    results[method_name] = True
                else:
                    print(f"    ❌ {method_name} failed")
                    print(f"      Error: {result.stderr.strip()}")
                    results[method_name] = False
            except Exception as e:
                print(f"    ❌ {method_name} test failed: {e}")
                results[method_name] = False
        
        self.results['authentication'] = results
        return results
    
    def test_common_shares(self) -> Dict[str, bool]:
        """Test access to common Windows shares."""
        print("\n📁 Testing common share access...")
        
        common_shares = ['C$', 'ADMIN$', 'IPC$', 'TestShare', 'Share', 'Public']
        results = {}
        
        for share in common_shares:
            print(f"  Testing share: {share}")
            try:
                if self.username and self.password:
                    cmd = ['smbclient', f'//{self.target_ip}/{share}', '-U', self.username, '-p', self.password, '-c', 'ls']
                elif self.username:
                    cmd = ['smbclient', f'//{self.target_ip}/{share}', '-U', self.username, '-N', '-c', 'ls']
                else:
                    cmd = ['smbclient', f'//{self.target_ip}/{share}', '-U', '', '-N', '-c', 'ls']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"    ✅ {share} is accessible")
                    results[share] = True
                else:
                    print(f"    ❌ {share} not accessible")
                    print(f"      Error: {result.stderr.strip()}")
                    results[share] = False
            except Exception as e:
                print(f"    ❌ {share} test failed: {e}")
                results[share] = False
        
        self.results['shares'] = results
        return results
    
    def test_network_connectivity(self) -> Dict[str, bool]:
        """Test basic network connectivity."""
        print("\n🌐 Testing network connectivity...")
        
        tests = {
            'ping': f'ping -c 1 {self.target_ip}',
            'traceroute': f'traceroute {self.target_ip}',
            'telnet_445': f'telnet {self.target_ip} 445'
        }
        
        results = {}
        for test_name, command in tests.items():
            print(f"  Testing {test_name}...")
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    print(f"    ✅ {test_name} successful")
                    results[test_name] = True
                else:
                    print(f"    ❌ {test_name} failed")
                    results[test_name] = False
            except Exception as e:
                print(f"    ❌ {test_name} test failed: {e}")
                results[test_name] = False
        
        self.results['network'] = results
        return results
    
    def generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on test results."""
        recommendations = []
        
        if not self.results.get('port_445', False):
            recommendations.append("🔒 Port 445 is blocked - Check Windows Firewall inbound rules for 'File and Printer Sharing (SMB-In)'")
        
        smb_versions = self.results.get('smb_versions', {})
        if not any(smb_versions.values()):
            recommendations.append("🔄 No SMB versions supported - Check SMB server configuration")
        elif not smb_versions.get('SMB1', False):
            recommendations.append("🔄 SMB1 is disabled - Consider enabling for legacy compatibility")
        
        auth_results = self.results.get('authentication', {})
        if not any(auth_results.values()):
            recommendations.append("🔐 All authentication methods failed - Check Windows security policies and provide valid credentials")
        
        shares = self.results.get('shares', {})
        if not any(shares.values()):
            recommendations.append("📁 No shares accessible - Check share permissions and ensure shares are published")
        
        if self.results.get('port_445', False) and not any(auth_results.values()):
            recommendations.append("🔐 Port 445 open but authentication required - Provide valid Windows credentials")
        
        return recommendations
    
    def run_full_diagnostics(self) -> Dict:
        """Run all diagnostic tests."""
        print(f"🚀 Starting SMB diagnostics for {self.target_ip}")
        print("=" * 50)
        
        # Run all tests
        self.test_port_connectivity()
        self.test_network_connectivity()
        self.test_smb_versions()
        self.test_authentication_methods()
        self.test_common_shares()
        
        # Generate recommendations
        # recommendations = self.generate_recommendations()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        for category, results in self.results.items():
            print(f"\n{category.upper()}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}")
            else:
                status = "✅" if results else "❌"
                print(f"  {status} {category}")
        
        # Remove recommendations output for production
        # if recommendations:
        #     print(f"\n💡 RECOMMENDATIONS:")
        #     for i, rec in enumerate(recommendations, 1):
        #         print(f"  {i}. {rec}")
        
        # Save results to file
        output_file = f"smb_diagnostics_{self.target_ip}_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'target_ip': self.target_ip,
                'timestamp': time.time(),
                'results': self.results
                # 'recommendations': recommendations
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        
        return self.results

def main():
    parser = argparse.ArgumentParser(description='SMB Connectivity Diagnostics Tool')
    parser.add_argument('target_ip', help='Target IP address')
    parser.add_argument('-u', '--username', help='Username for authentication')
    parser.add_argument('-p', '--password', help='Password for authentication')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    
    args = parser.parse_args()
    
    diagnostics = SMBDiagnostics(args.target_ip, args.username, args.password)
    results = diagnostics.run_full_diagnostics()
    
    if args.json:
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main() 