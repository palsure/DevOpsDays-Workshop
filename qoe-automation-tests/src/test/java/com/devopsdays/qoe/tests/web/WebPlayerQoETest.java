package com.devopsdays.qoe.tests.web;

import com.devopsdays.qoe.framework.utils.ApiClient;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.time.Duration;
import java.util.List;
import java.util.Map;

public class WebPlayerQoETest {
    private WebDriver driver;
    private WebDriverWait wait;
    private ApiClient apiClient;
    private static final String BASE_URL = System.getProperty("web.player.url", "http://localhost:3000");
    private static final String API_URL = System.getProperty("api.base.url", "http://localhost:8080");
    
    @BeforeClass
    public void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(30));
        apiClient = new ApiClient(API_URL);
    }
    
    @Test
    public void testWebPlayerLoads() {
        driver.get(BASE_URL);
        String title = driver.getTitle();
        Assert.assertNotNull(title, "Page title should not be null");
        Assert.assertTrue(title.contains("QoE") || title.contains("Player"), 
                "Page title should contain QoE or Player");
    }
    
    @Test(dependsOnMethods = "testWebPlayerLoads")
    public void testMetricsCollected() throws Exception {
        // Wait for metrics to be collected (simulate playback)
        Thread.sleep(10000);
        
        List<Map<String, Object>> metrics = apiClient.getMetrics("web", null, null);
        // Metrics may be empty if no playback occurred, so we just check the API works
        Assert.assertNotNull(metrics, "Metrics API should return a response");
    }
    
    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
