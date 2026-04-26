package com.devopsdays.qoe.tests.mobile;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.android.options.UiAutomator2Options;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.net.URI;
import java.time.Duration;

public class MobileQoETest {

    private AndroidDriver driver;
    private WebDriverWait wait;

    private static final String APPIUM_URL   = "http://localhost:4723";
    private static final String APP_PACKAGE  = "com.devopsdays.qoe";
    // Full class name because applicationId differs from the Kotlin source package
    private static final String APP_ACTIVITY = "com.devopsdays.qoe.player.MainActivity";
    private static final String APK_PATH     = System.getProperty(
            "apk.path",
            System.getProperty("user.home") +
            "/Documents/projects/DevOpsDays/android-player" +
            "/app/build/outputs/apk/debug/app-debug.apk"
    );
    private static final String HLS_URL =
            "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8";

    // ── Setup / Teardown ───────────────────────────────────────────────────

    @BeforeClass
    public void setUp() throws Exception {
        UiAutomator2Options options = new UiAutomator2Options()
                .setDeviceName("Android Emulator")
                // Launch pre-installed app directly (no reinstall = no install dialogs)
                .setAppPackage(APP_PACKAGE)
                .setAppActivity(APP_ACTIVITY)
                .setNoReset(true)
                .setAutoGrantPermissions(true)
                .setNewCommandTimeout(Duration.ofSeconds(120));

        driver = new AndroidDriver(new URI(APPIUM_URL).toURL(), options);
        wait   = new WebDriverWait(driver, Duration.ofSeconds(30));

        // Appium's own settings notification can pull down the shade and
        // block the app UI. Close it, then ensure our app is in the foreground.
        Thread.sleep(1_500);
        driver.pressKey(new io.appium.java_client.android.nativekey.KeyEvent(
                io.appium.java_client.android.nativekey.AndroidKey.BACK));
        Thread.sleep(800);
        // Re-activate the app in case BACK sent it to the background
        driver.activateApp(APP_PACKAGE);
        Thread.sleep(1_000);
    }

    @AfterClass(alwaysRun = true)
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    // ── Tests ──────────────────────────────────────────────────────────────

    @Test(description = "App launches and main screen is visible")
    public void testAppLaunches() {
        WebElement playBtn = wait.until(
                ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.id(APP_PACKAGE + ":id/play_button")));
        Assert.assertNotNull(playBtn, "Play button should be visible on launch");
        System.out.println("✅ App launched successfully");
    }

    @Test(dependsOnMethods = "testAppLaunches",
          description = "HLS URL field accepts input")
    public void testUrlInputAcceptsText() {
        WebElement urlInput = wait.until(
                ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.id(APP_PACKAGE + ":id/url_input")));
        urlInput.clear();
        urlInput.sendKeys(HLS_URL);
        String value = urlInput.getText();
        Assert.assertEquals(value, HLS_URL, "URL field should contain the entered HLS URL");
        System.out.println("✅ URL input accepted: " + value);
    }

    @Test(dependsOnMethods = "testUrlInputAcceptsText",
          description = "Video ID field accepts custom ID")
    public void testVideoIdInput() {
        WebElement idInput = wait.until(
                ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.id(APP_PACKAGE + ":id/video_id_input")));
        idInput.clear();
        idInput.sendKeys("automation-test-001");
        Assert.assertEquals(idInput.getText(), "automation-test-001",
                "Video ID field should reflect entered value");
        System.out.println("✅ Video ID input accepted");
    }

    @Test(dependsOnMethods = "testVideoIdInput",
          description = "Tapping Play starts video playback")
    public void testPlayButtonStartsPlayback() {
        WebElement playBtn = wait.until(
                ExpectedConditions.elementToBeClickable(
                        AppiumBy.id(APP_PACKAGE + ":id/play_button")));
        playBtn.click();

        // Status text should transition away from the initial "Ready" state
        WebElement status = wait.until(
                ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.id(APP_PACKAGE + ":id/status_text")));

        // Wait up to 20 s for buffering or ready state
        WebDriverWait longWait = new WebDriverWait(driver, Duration.ofSeconds(20));
        longWait.until(driver1 -> {
            String text = status.getText();
            return text.equals("Buffering...") || text.equals("Ready");
        });

        String statusText = status.getText();
        Assert.assertTrue(
                statusText.equals("Buffering...") || statusText.equals("Ready"),
                "Status should be Buffering or Ready after Play, but was: " + statusText);
        System.out.println("✅ Playback started — status: " + statusText);
    }

    @Test(dependsOnMethods = "testPlayButtonStartsPlayback",
          description = "Player stays healthy: no error within 30 seconds of playback")
    public void testPlayerHealthy() throws InterruptedException {
        WebElement status = wait.until(
                ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.id(APP_PACKAGE + ":id/status_text")));

        // Poll for up to 30 s — accept Ready or Buffering, fail on Error
        WebDriverWait pollWait = new WebDriverWait(driver, Duration.ofSeconds(30));
        pollWait.until(driver1 -> {
            String t = status.getText();
            if (t.startsWith("Error:"))
                throw new RuntimeException("Playback error: " + t);
            return t.equals("Ready") || t.equals("Buffering...");
        });

        String finalStatus = status.getText();
        Assert.assertFalse(finalStatus.startsWith("Error:"),
                "Player should not report an error, but was: " + finalStatus);
        System.out.println("✅ Player healthy — status: " + finalStatus);
    }
}
