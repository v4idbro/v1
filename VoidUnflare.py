#!/usr/bin/env python3
import requests
import socket
import sys
import time
from urllib.parse import urlparse
import subprocess
import os

class VoidUnflare:
    def __init__(self):
        self.target_url = ""
        self.real_ip = None
        self.PURPLE = '\033[95m'
        self.LIGHT_PURPLE = '\033[94m'
        self.END = '\033[0m'
        self.progress = 0
        
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
            time.sleep(0.35)
        
        print()
        time.sleep(0.3)
        print(f"{self.LIGHT_PURPLE}Made By v4idbro{self.END}")
        print()
    
    def update_progress(self, value):
        self.progress = value
        print(f"{self.LIGHT_PURPLE}[{value}%]{self.END}", end=" ", flush=True)
    
    def show_menu(self):
        print(f"{self.LIGHT_PURPLE}[1] Start{self.END}")
        print()
        choice = input(f"{self.LIGHT_PURPLE}[>] Select option: {self.END}").strip()
        
        if choice == "1":
            self.get_target_url()
        else:
            print(f"{self.PURPLE}Invalid option{self.END}")
            sys.exit(0)
    
    def get_target_url(self):
        url = input(f"{self.LIGHT_PURPLE}[>] Target URL/Domain: {self.END}").strip()
        
        if not url:
            print(f"{self.PURPLE}No URL provided{self.END}")
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
    
    def resolve_dns(self):
        domain = self.extract_domain()
        
        if not domain:
            return False
        
        try:
            ip = socket.gethostbyname(domain)
            print(f"{self.LIGHT_PURPLE}DNS: {domain} -> {ip}{self.END}")
            self.real_ip = ip
            return True
        except socket.gaierror:
            return False
    
    def check_subdomains(self):
        domain = self.extract_domain()
        if not domain:
            return False
            
        subdomains = ['www', 'mail', 'ftp', 'api', 'admin', 'webmail', 'smtp', 'direct', 'cpanel', 'whm']
        found = False
        
        for sub in subdomains:
            subdomain = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(subdomain)
                print(f"{self.LIGHT_PURPLE}Subdomain: {subdomain} -> {ip}{self.END}")
                if not self.real_ip:
                    self.real_ip = ip
                found = True
            except:
                pass
        
        return found
    
    def try_http_headers(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.target_url, headers=headers, timeout=5, verify=False, allow_redirects=True)
            
            if 'Server' in response.headers:
                print(f"{self.LIGHT_PURPLE}Server: {response.headers['Server']}{self.END}")
            
            if 'X-Original-IP' in response.headers:
                print(f"{self.LIGHT_PURPLE}X-Original-IP: {response.headers['X-Original-IP']}{self.END}")
                self.real_ip = response.headers['X-Original-IP']
                return True
            
            if 'CF-Ray' in response.headers:
                print(f"{self.LIGHT_PURPLE}CloudFlare CF-Ray: {response.headers['CF-Ray']}{self.END}")
            
            if 'X-Powered-By' in response.headers:
                print(f"{self.LIGHT_PURPLE}Powered-By: {response.headers['X-Powered-By']}{self.END}")
            
        except Exception as e:
            pass
        
        return False
    
    def test_direct_connection(self):
        domain = self.extract_domain()
        
        if not domain:
            return False
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((domain, 80))
            sock.close()
            
            if result == 0:
                ip = socket.gethostbyname(domain)
                print(f"{self.LIGHT_PURPLE}Direct Connection: {ip}{self.END}")
                if not self.real_ip:
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
            print(f"{self.LIGHT_PURPLE}Reverse DNS: {hostname[0]}{self.END}")
            return True
        except:
            pass
        
        return False
    
    def check_whois_info(self):
        if not self.real_ip:
            return False
        
        try:
            response = requests.get(f"https://ipapi.co/{self.real_ip}/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                country = data.get('country_name', 'N/A')
                city = data.get('city', 'N/A')
                org = data.get('org', 'N/A')
                print(f"{self.LIGHT_PURPLE}Location: {city}, {country}{self.END}")
                print(f"{self.LIGHT_PURPLE}ISP: {org}{self.END}")
                return True
        except:
            pass
        
        return False
    
    def run_java_scan(self):
        try:
            result = subprocess.run(['java', 'VoidUnflareJava', self.target_url], 
                                   capture_output=True, text=True, timeout=30)
            if result.stdout:
                output = result.stdout.strip()
                if output and "Java" in output:
                    print(output)
        except:
            pass
    
    def run_ruby_scan(self):
        try:
            result = subprocess.run(['ruby', 'VoidUnflare.rb', self.target_url], 
                                   capture_output=True, text=True, timeout=30)
            if result.stdout:
                output = result.stdout.strip()
                if output and "Ruby" in output:
                    print(output)
        except:
            pass
    
    def start_multi_scan(self):
        total_steps = 10
        step = 0
        
        print(f"{self.PURPLE}Scanning", end="")
        
        step += 1
        self.update_progress(step * 10)
        self.try_http_headers()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        self.resolve_dns()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        self.test_direct_connection()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        self.check_subdomains()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        
        if self.real_ip:
            self.check_reverse_dns()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        
        if self.real_ip:
            self.check_whois_info()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        self.run_java_scan()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        self.run_ruby_scan()
        
        step += 1
        self.update_progress(step * 10)
        time.sleep(0.3)
        
        print(f"\n")
        
        if self.real_ip:
            print(f"{self.LIGHT_PURPLE}Real IP: {self.real_ip}{self.END}")
            print(f"{self.LIGHT_PURPLE}Target: {self.target_url}{self.END}")
            print(f"{self.LIGHT_PURPLE}Domain: {self.extract_domain()}{self.END}")
        else:
            print(f"{self.PURPLE}Could not determine real IP{self.END}")
        
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
