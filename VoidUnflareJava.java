import java.io.*;
import java.net.*;
import java.util.*;
import java.util.regex.*;

public class VoidUnflareJava {
    private static final String PURPLE = "\u001B[35m";
    private static final String RESET = "\u001B[0m";
    
    private String targetUrl = "";
    private String realIp = null;
    private Set<String> cloudflareIps = new HashSet<>();
    
    public VoidUnflareJava(String url) {
        this.targetUrl = url;
    }
    
    public String extractDomain() {
        try {
            URL url = new URL(targetUrl);
            return url.getHost();
        } catch (Exception e) {
            return null;
        }
    }
    
    public boolean isCloudflareIp(String ip) {
        if (ip == null || ip.isEmpty()) return false;
        
        String[] cloudflareRanges = {
            "103.21.244.0", "103.22.200.0", "103.31.4.0",
            "104.16.0.0", "108.162.192.0", "131.0.72.0",
            "141.101.64.0", "162.125.18.0", "162.158.0.0",
            "172.64.0.0", "173.245.48.0", "188.114.96.0",
            "190.93.240.0", "197.234.240.0", "198.41.128.0"
        };
        
        for (String range : cloudflareRanges) {
            if (ip.startsWith(range.substring(0, range.lastIndexOf(".")))) {
                cloudflareIps.add(ip);
                return true;
            }
        }
        
        return false;
    }
    
    public void resolveDns() {
        String domain = extractDomain();
        
        if (domain == null) {
            return;
        }
        
        try {
            InetAddress addr = InetAddress.getByName(domain);
            String ip = addr.getHostAddress();
            if (ip != null && !isCloudflareIp(ip)) {
                System.out.println(PURPLE + "Java DNS: " + ip + RESET);
                if (this.realIp == null) {
                    this.realIp = ip;
                }
            }
        } catch (UnknownHostException e) {
        }
    }
    
    public void checkSubdomains() {
        String domain = extractDomain();
        if (domain == null) return;
        
        String[] subdomains = {"www", "mail", "ftp", "api", "admin", "webmail", "smtp", "direct", "cpanel", "whm", "ns1", "mx", "cdn", "origin", "backend"};
        
        for (String sub : subdomains) {
            String subdomain = sub + "." + domain;
            try {
                InetAddress addr = InetAddress.getByName(subdomain);
                String ip = addr.getHostAddress();
                if (ip != null && !isCloudflareIp(ip) && !cloudflareIps.contains(ip)) {
                    System.out.println(PURPLE + "Java Subdomain: " + subdomain + " -> " + ip + RESET);
                    if (this.realIp == null) {
                        this.realIp = ip;
                    }
                }
            } catch (UnknownHostException e) {
            }
        }
    }
    
    public void tryHttpHeaders() {
        try {
            URL url = new URL(targetUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(6000);
            connection.setReadTimeout(6000);
            connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            
            Map<String, List<String>> headers = connection.getHeaderFields();
            
            if (headers.containsKey("Server")) {
                System.out.println(PURPLE + "Java Server: " + headers.get("Server").get(0) + RESET);
            }
            
            if (headers.containsKey("X-Original-IP")) {
                String ip = headers.get("X-Original-IP").get(0);
                if (ip != null && !isCloudflareIp(ip)) {
                    System.out.println(PURPLE + "Java X-Original-IP: " + ip + RESET);
                    if (this.realIp == null) {
                        this.realIp = ip;
                    }
                }
            }
            
            connection.disconnect();
        } catch (Exception e) {
        }
    }
    
    public void testDirectConnection() {
        String domain = extractDomain();
        
        if (domain == null) return;
        
        try {
            Socket socket = new Socket();
            socket.connect(new InetSocketAddress(domain, 80), 3000);
            InetAddress addr = socket.getInetAddress();
            String ip = addr.getHostAddress();
            if (ip != null && !isCloudflareIp(ip)) {
                System.out.println(PURPLE + "Java Direct: " + ip + RESET);
                if (this.realIp == null) {
                    this.realIp = ip;
                }
            }
            socket.close();
        } catch (Exception e) {
        }
    }
    
    public void checkReverseIp() {
        String domain = extractDomain();
        if (domain == null) return;
        
        try {
            URL url = new URL("https://api.hackertarget.com/reverseiplookup/?host=" + domain);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(6000);
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.matches("\\d+\\.\\d+\\.\\d+\\.\\d+")) {
                    if (!isCloudflareIp(line) && !cloudflareIps.contains(line)) {
                        System.out.println(PURPLE + "Java Reverse: " + line + RESET);
                        if (this.realIp == null) {
                            this.realIp = line;
                        }
                        break;
                    }
                }
            }
            reader.close();
            connection.disconnect();
        } catch (Exception e) {
        }
    }
    
    public void startScan() {
        tryHttpHeaders();
        
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
        }
        
        resolveDns();
        
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
        }
        
        testDirectConnection();
        
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
        }
        
        checkReverseIp();
        
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
        }
        
        checkSubdomains();
    }
    
    public static void main(String[] args) {
        if (args.length < 1) {
            System.exit(1);
        }
        
        try {
            VoidUnflareJava tool = new VoidUnflareJava(args[0]);
            tool.startScan();
        } catch (Exception e) {
            System.exit(0);
        }
    }
}
