import java.io.*;
import java.net.*;
import java.util.*;

public class VoidUnflareJava {
    private static final String PURPLE = "\u001B[95m";
    private static final String LIGHT_PURPLE = "\u001B[94m";
    private static final String RESET = "\u001B[0m";
    
    private String targetUrl = "";
    private String realIp = null;
    
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
    
    public void resolveDns() {
        String domain = extractDomain();
        
        if (domain == null) {
            return;
        }
        
        try {
            InetAddress addr = InetAddress.getByName(domain);
            String ip = addr.getHostAddress();
            System.out.println(LIGHT_PURPLE + "Java DNS: " + domain + " -> " + ip + RESET);
            this.realIp = ip;
        } catch (UnknownHostException e) {
        }
    }
    
    public void checkSubdomains() {
        String domain = extractDomain();
        if (domain == null) return;
        
        String[] subdomains = {"www", "mail", "ftp", "api", "admin", "webmail", "smtp", "direct", "cpanel", "whm"};
        
        for (String sub : subdomains) {
            String subdomain = sub + "." + domain;
            try {
                InetAddress addr = InetAddress.getByName(subdomain);
                String ip = addr.getHostAddress();
                System.out.println(LIGHT_PURPLE + "Java Subdomain: " + subdomain + " -> " + ip + RESET);
                if (this.realIp == null) {
                    this.realIp = ip;
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
            connection.setConnectTimeout(5000);
            connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            
            Map<String, List<String>> headers = connection.getHeaderFields();
            
            if (headers.containsKey("Server")) {
                System.out.println(LIGHT_PURPLE + "Java Server: " + headers.get("Server").get(0) + RESET);
            }
            
            if (headers.containsKey("CF-Ray")) {
                System.out.println(LIGHT_PURPLE + "Java CloudFlare: " + headers.get("CF-Ray").get(0) + RESET);
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
            System.out.println(LIGHT_PURPLE + "Java Direct: " + ip + RESET);
            if (this.realIp == null) {
                this.realIp = ip;
            }
            socket.close();
        } catch (Exception e) {
        }
    }
    
    public void startScan() {
        tryHttpHeaders();
        
        try {
            Thread.sleep(300);
        } catch (InterruptedException e) {
        }
        
        resolveDns();
        
        try {
            Thread.sleep(300);
        } catch (InterruptedException e) {
        }
        
        testDirectConnection();
        
        try {
            Thread.sleep(300);
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
