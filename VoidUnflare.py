#!/usr/bin/env python3
import requests
import socket
import sys
import time
from urllib.parse import urlparse
import subprocess
import os
import re

class VoidUnflare:
    def __init__(self):
        self.target_url = ""
        self.real_ip = None
        self.PURPLE = '\033[35m'
        self.END = '\033[0m'
        self.progress = 0
        self.cloudflare_ips = set()
        
    def print_banner_animated(self):
        banner_lines = [
            "    //    //  ///////   ///  ///////    ///   ///  ///   ///  ///////  ///         ///////  ///////   ///////",
            "     //    //  //   //   ///  //    //   ///   ///  ////  ///  //       ///         //   //  //   //   //     ",
            "     //    //  //   //   ///  //    //   ///   ///  // // ///  ///////  ///         ///////  //////    ///////",
            "      //  //   //   //   ///  //    //   ///   ///  //  //////  //       ///         //   //  //   //   //     ",
            "       ////    ///////   ///  ///////    /////////  //   ////  //       //////////  //   //  //    //  ///////",
        ]
        
        print()
        for line in banner_lines:
            print(f"{self.PURPLE}{line}{self.END}")
            time.sleep(0.25)
        
        print()
        print(f"{self.PURPLE}Made By v4idbro{self.END}")
        print()
    
    def update_progress(self, value):
        self.progress = value
        print(f"{self.PURPLE}[{value}%]{self.END}", end=" ", flush=True)
    
    def show_menu(self):
        print(f"{self.PURPLE}[1] Start Scan{self.END}")
        print()
        choice = input(f"{self.PURPLE}[>] Option: {self.END}").strip()
        
        if choice == "1":
            self.get_target_url()
        else:
            print(f"{self.PURPLE}Invalid{self.END}")
            sys.exit(0)
    
    def get_target_url(self):
        url = input(f"{self.PURPLE}[>] Target: {self.END}").strip()
        
        if not url:
            print(f"{self.PURPLE}Error: No URL{self.END}")
            return False
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        self.target_url = url
        print()
        self.start_multi_scan()
        return True
    
    def extract_domain(self):
        try:
            parsed = urlparse(self.target_url)
            domain = parsed.netloc
            return domain
        except:
            return None
    
    def is_cloudflare_ip(self, ip):
        if not ip:
            return False
            
        cloudflare_ranges = [
            '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
            '104.16.0.0/12', '108.162.192.0/18', '131.0.72.0/22',
            '141.101.64.0/18', '162.125.18.0/23', '162.158.0.0/15',
            '172.64.0.0/13', '173.245.48.0/20', '188.114.96.0/20',
            '190.93.240.0/20', '197.234.240.0/22', '198.41.128.0/17',
        ]
        
        try:
            from ipaddress import ip_address, ip_network
            ip_obj = ip_address(ip)
            for cf_range in cloudflare_ranges:
                if ip_obj in ip_network(cf_range):
                    self.cloudflare_ips.add(ip)
                    return True
        except:
            pass
        
        return False
    
    def check_dns_history(self):
        domain = self.extract_domain()
        if not domain:
            return False
        
        try:
            response = requests.get(f"https://dns.bufferover.run/dns?q=.{domain}", timeout=6, verify=False)
            if response.status_code == 200:
                data = response.json()
                if 'FDNS_A' in data:
                    for record in data['FDNS_A'][:15]:
                        if ',' in record:
                            parts = record.split(',')
                            if len(parts) >= 2:
                                ip = parts[1].strip()
                                if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                                    print(f"{self.PURPLE}History: {ip}{self.END}")
                                    if not self.real_ip:
                                        self.real_ip = ip
                                    return True
        except:
            pass
        
        return False
    
    def check_crt_sh(self):
        domain = self.extract_domain()
        if not domain:
            return False
        
        try:
            response = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=6, verify=False)
            if response.status_code == 200:
                certs = response.json()
                for cert in certs[:20]:
                    name_value = cert.get('name_value', '')
                    ips = re.findall(r'\d+\.\d+\.\d+\.\d+', name_value)
                    for ip in ips:
                        if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                            print(f"{self.PURPLE}Certificate: {ip}{self.END}")
                            if not self.real_ip:
                                self.real_ip = ip
                            return True
        except:
            pass
        
        return False
    
    def check_reverse_ip_lookup(self):
        domain = self.extract_domain()
        if not domain:
            return False
        
        try:
            response = requests.get(f"https://api.hackertarget.com/reverseiplookup/?host={domain}", timeout=6, verify=False)
            if response.status_code == 200 and response.text and 'error' not in response.text.lower():
                ips = response.text.strip().split('\n')
                for ip in ips[:10]:
                    ip = ip.strip()
                    if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                        print(f"{self.PURPLE}Reverse: {ip}{self.END}")
                        if not self.real_ip:
                            self.real_ip = ip
                        return True
        except:
            pass
        
        return False
    
    def check_whois_api(self):
        domain = self.extract_domain()
        if not domain:
            return False
        
        try:
            response = requests.get(f"https://www.whois.com/whois/{domain}", timeout=6, verify=False)
            if response.status_code == 200:
                ips = re.findall(r'\d+\.\d+\.\d+\.\d+', response.text)
                for ip in ips:
                    if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                        print(f"{self.PURPLE}WHOIS: {ip}{self.END}")
                        if not self.real_ip:
                            self.real_ip = ip
                        return True
        except:
            pass
        
        return False
    
    def try_http_headers(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.target_url, headers=headers, timeout=6, verify=False, allow_redirects=True)
            
            if 'Server' in response.headers:
                print(f"{self.PURPLE}Server: {response.headers['Server']}{self.END}")
            
            if 'X-Original-IP' in response.headers:
                ip = response.headers['X-Original-IP']
                if not self.is_cloudflare_ip(ip):
                    print(f"{self.PURPLE}X-Original-IP: {ip}{self.END}")
                    self.real_ip = ip
                    return True
            
        except:
            pass
        
        return False
    
    def check_subdomains(self):
        domain = self.extract_domain()
        if not domain:
            return False
            
        subdomains = ['www', 'mail', 'ftp', 'api', 'admin', 'webmail', 'smtp', 'direct', 'cpanel', 'whm', 'ns1', 'mx', 'cdn', 'origin', 'backend', 'server']
        
        for sub in subdomains:
            subdomain = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(subdomain)
                if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                    print(f"{self.PURPLE}Subdomain: {subdomain} -> {ip}{self.END}")
                    if not self.real_ip:
                        self.real_ip = ip
                    return True
            except:
                pass
        
        return False
    
    def resolve_dns(self):
        domain = self.extract_domain()
        
        if not domain:
            return False
        
        try:
            ip = socket.gethostbyname(domain)
            if ip and not self.is_cloudflare_ip(ip):
                print(f"{self.PURPLE}DNS: {domain} -> {ip}{self.END}")
                self.real_ip = ip
                return True
        except:
            pass
        
        return False
    
    def check_reverse_dns(self):
        if not self.real_ip:
            return False
        
        try:
            hostname = socket.gethostbyaddr(self.real_ip)
            print(f"{self.PURPLE}Hostname: {hostname[0]}{self.END}")
            return True
        except:
            pass
        
        return False
    
    def check_whois_info(self):
        if not self.real_ip:
            return False
        
        try:
            response = requests.get(f"https://ipapi.co/{self.real_ip}/json/", timeout=6, verify=False)
            if response.status_code == 200:
                data = response.json()
                country = data.get('country_name', 'N/A')
                city = data.get('city', 'N/A')
                org = data.get('org', 'N/A')
                print(f"{self.PURPLE}Location: {city}, {country}{self.END}")
                print(f"{self.PURPLE}Provider: {org}{self.END}")
                return True
        except:
            pass
        
        return False
    
    def run_java_scan(self):
        try:
            result = subprocess.run(['java', 'VoidUnflareJava', self.target_url], 
                                   capture_output=True, text=True, timeout=20)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and 'Java' in line:
                        print(line)
                        ips = re.findall(r'\d+\.\d+\.\d+\.\d+', line)
                        for ip in ips:
                            if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                                if not self.real_ip:
                                    self.real_ip = ip
        except:
            pass
    
    def run_ruby_scan(self):
        try:
            result = subprocess.run(['ruby', 'VoidUnflare.rb', self.target_url], 
                                   capture_output=True, text=True, timeout=20)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and 'Ruby' in line:
                        print(line)
                        ips = re.findall(r'\d+\.\d+\.\d+\.\d+', line)
                        for ip in ips:
                            if ip and not self.is_cloudflare_ip(ip) and ip not in self.cloudflare_ips:
                                if not self.real_ip:
                                    self.real_ip = ip
        except:
            pass
    
    def start_multi_scan(self):
        print(f"{self.PURPLE}Scanning", end="")
        
        step = 1
        self.update_progress(step * 10)
        self.check_dns_history()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.check_crt_sh()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.check_reverse_ip_lookup()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.try_http_headers()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.resolve_dns()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.check_whois_api()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.check_subdomains()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        
        if self.real_ip:
            self.check_reverse_dns()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        
        if self.real_ip:
            self.check_whois_info()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.2)
        self.run_java_scan()
        self.run_ruby_scan()
        
        print(f"\n")
        
        if self.real_ip:
            print(f"{self.PURPLE}Origin IP: {self.real_ip}{self.END}")
            print(f"{self.PURPLE}Target: {self.target_url}{self.END}")
            print(f"{self.PURPLE}Domain: {self.extract_domain()}{self.END}")
        else:
            print(f"{self.PURPLE}No origin IP found{self.END}")
        
        print()
    
    def run(self):
        self.print_banner_animated()
        self.show_menu()

if __name__ == "__main__":
    tool = VoidUnflare()
    try:
        tool.run()
    except KeyboardInterrupt:
        print(f"\n\n{tool.PURPLE}Interrupted{tool.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{tool.PURPLE}Error: {str(e)}{tool.END}")
        sys.exit(1)
