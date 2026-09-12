#!/usr/bin/env ruby

require 'net/http'
require 'uri'
require 'socket'
require 'json'

class VoidUnflareHelper
  PURPLE = "\e[35m"
  RESET = "\e[0m"
  
  def initialize(target_url)
    @target_url = target_url
    @real_ip = nil
    @cloudflare_ips = Set.new
  end
  
  def extract_domain
    begin
      uri = URI.parse(@target_url)
      uri.host
    rescue
      nil
    end
  end
  
  def is_cloudflare_ip(ip)
    return false if ip.nil? || ip.empty?
    
    cloudflare_ranges = [
      '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
      '104.16.0.0/12', '108.162.192.0/18', '131.0.72.0/22',
      '141.101.64.0/18', '162.125.18.0/23', '162.158.0.0/15',
      '172.64.0.0/13', '173.245.48.0/20', '188.114.96.0/20',
      '190.93.240.0/20', '197.234.240.0/22', '198.41.128.0/17',
    ]
    
    begin
      require 'ipaddr'
      ip_obj = IPAddr.new(ip)
      cloudflare_ranges.each do |cf_range|
        if IPAddr.new(cf_range).include?(ip_obj)
          @cloudflare_ips.add(ip)
          return true
        end
      end
    rescue
    end
    
    false
  end
  
  def resolve_dns
    domain = extract_domain
    
    return false if domain.nil?
    
    begin
      ip = Socket.getaddrinfo(domain, nil, Socket::AF_INET).first[3]
      if ip && !is_cloudflare_ip(ip) && !@cloudflare_ips.include?(ip)
        puts "#{PURPLE}Ruby DNS: #{ip}#{RESET}"
        @real_ip = ip if @real_ip.nil?
        return true
      end
    rescue SocketError
    end
    
    false
  end
  
  def check_subdomains
    domain = extract_domain
    return false if domain.nil?
    
    subdomains = ['www', 'mail', 'ftp', 'api', 'admin', 'webmail', 'smtp', 'direct', 'cpanel', 'whm', 'ns1', 'mx', 'cdn', 'origin', 'backend']
    found = false
    
    subdomains.each do |sub|
      subdomain = "#{sub}.#{domain}"
      begin
        ip = Socket.getaddrinfo(subdomain, nil, Socket::AF_INET).first[3]
        if ip && !is_cloudflare_ip(ip) && !@cloudflare_ips.include?(ip)
          puts "#{PURPLE}Ruby Subdomain: #{subdomain} -> #{ip}#{RESET}"
          @real_ip = ip if @real_ip.nil?
          found = true
        end
      rescue SocketError
      end
    end
    
    found
  end
  
  def try_http_headers
    begin
      uri = URI.parse(@target_url)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == 'https'
      http.open_timeout = 6
      http.read_timeout = 6
      
      request = Net::HTTP::Get.new(uri.request_uri)
      request['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      
      response = http.request(request)
      
      if response['Server']
        puts "#{PURPLE}Ruby Server: #{response['Server']}#{RESET}"
      end
      
      if response['X-Original-IP']
        ip = response['X-Original-IP']
        if !is_cloudflare_ip(ip)
          puts "#{PURPLE}Ruby X-Original-IP: #{ip}#{RESET}"
          @real_ip = ip if @real_ip.nil?
        end
      end
      
      true
    rescue => e
      false
    end
  end
  
  def test_direct_connection
    domain = extract_domain
    
    return false if domain.nil?
    
    begin
      socket = Socket.new(:INET, :STREAM)
      begin
        socket.connect_nonblock(Socket.pack_sockaddr_in(80, domain))
      rescue Errno::EINPROGRESS
        if IO.select(nil, [socket], nil, 3)
          begin
            socket.connect_nonblock(Socket.pack_sockaddr_in(80, domain))
          rescue Errno::EISCONN
          end
        end
      end
      
      ip = Socket.getaddrinfo(domain, nil, Socket::AF_INET).first[3]
      if ip && !is_cloudflare_ip(ip) && !@cloudflare_ips.include?(ip)
        puts "#{PURPLE}Ruby Direct: #{ip}#{RESET}"
        @real_ip = ip if @real_ip.nil?
      end
      socket.close
      true
    rescue => e
      socket.close if socket
      false
    end
  end
  
  def check_reverse_ip
    domain = extract_domain
    return false if domain.nil?
    
    begin
      uri = URI.parse("https://api.hackertarget.com/reverseiplookup/?host=#{domain}")
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = true
      http.open_timeout = 6
      http.read_timeout = 6
      
      response = http.get(uri.request_uri)
      
      if response.code == '200' && response.body && response.body !~ /error/i
        ips = response.body.strip.split("\n")
        ips.each do |ip|
          ip = ip.strip
          if ip && !is_cloudflare_ip(ip) && !@cloudflare_ips.include?(ip)
            puts "#{PURPLE}Ruby Reverse: #{ip}#{RESET}"
            @real_ip = ip if @real_ip.nil?
            return true
          end
        end
      end
    rescue => e
    end
    
    false
  end
  
  def check_dns_history
    domain = extract_domain
    return false if domain.nil?
    
    begin
      uri = URI.parse("https://dns.bufferover.run/dns?q=.#{domain}")
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = true
      http.open_timeout = 6
      http.read_timeout = 6
      
      response = http.get(uri.request_uri)
      
      if response.code == '200'
        data = JSON.parse(response.body)
        if data['FDNS_A']
          data['FDNS_A'][0..9].each do |record|
            if record.include?(',')
              parts = record.split(',')
              if parts.length >= 2
                ip = parts[1].strip
                if ip && !is_cloudflare_ip(ip) && !@cloudflare_ips.include?(ip)
                  puts "#{PURPLE}Ruby History: #{ip}#{RESET}"
                  @real_ip = ip if @real_ip.nil?
                  return true
                end
              end
            end
          end
        end
      end
    rescue => e
    end
    
    false
  end
  
  def start_scan
    check_dns_history
    sleep(0.2)
    
    check_reverse_ip
    sleep(0.2)
    
    try_http_headers
    sleep(0.2)
    
    resolve_dns
    sleep(0.2)
    
    test_direct_connection
    sleep(0.2)
    
    check_subdomains
  end
  
  def run
    start_scan
  end
end

if __FILE__ == $0
  if ARGV.empty?
    exit(1)
  end
  
  begin
    tool = VoidUnflareHelper.new(ARGV[0])
    tool.run
  rescue Interrupt
    exit(0)
  rescue => e
    exit(1)
  end
end
