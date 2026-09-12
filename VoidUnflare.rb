#!/usr/bin/env ruby

require 'net/http'
require 'uri'
require 'socket'

class VoidUnflareHelper
  PURPLE = "\e[95m"
  LIGHT_PURPLE = "\e[94m"
  RESET = "\e[0m"
  
  def initialize(target_url)
    @target_url = target_url
    @real_ip = nil
  end
  
  def extract_domain
    begin
      uri = URI.parse(@target_url)
      uri.host
    rescue
      nil
    end
  end
  
  def resolve_dns
    domain = extract_domain
    
    return false if domain.nil?
    
    begin
      ip = Socket.getaddrinfo(domain, nil, Socket::AF_INET).first[3]
      puts "#{LIGHT_PURPLE}Ruby DNS: #{domain} -> #{ip}#{RESET}"
      @real_ip = ip
      true
    rescue SocketError
      false
    end
  end
  
  def check_subdomains
    domain = extract_domain
    return false if domain.nil?
    
    subdomains = ['www', 'mail', 'ftp', 'api', 'admin', 'webmail', 'smtp', 'direct', 'cpanel', 'whm']
    found = false
    
    subdomains.each do |sub|
      subdomain = "#{sub}.#{domain}"
      begin
        ip = Socket.getaddrinfo(subdomain, nil, Socket::AF_INET).first[3]
        puts "#{LIGHT_PURPLE}Ruby Subdomain: #{subdomain} -> #{ip}#{RESET}"
        @real_ip = ip if @real_ip.nil?
        found = true
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
      http.open_timeout = 5
      http.read_timeout = 5
      
      request = Net::HTTP::Get.new(uri.request_uri)
      request['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      
      response = http.request(request)
      
      puts "#{LIGHT_PURPLE}Ruby Server: #{response['Server']}#{RESET}" if response['Server']
      puts "#{LIGHT_PURPLE}Ruby CloudFlare: #{response['CF-Ray']}#{RESET}" if response['CF-Ray']
      
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
      puts "#{LIGHT_PURPLE}Ruby Direct: #{ip}#{RESET}"
      @real_ip = ip if @real_ip.nil?
      socket.close
      true
    rescue => e
      socket.close if socket
      false
    end
  end
  
  def start_scan
    try_http_headers
    sleep(0.3)
    
    resolve_dns
    sleep(0.3)
    
    test_direct_connection
    sleep(0.3)
    
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
  end
end
