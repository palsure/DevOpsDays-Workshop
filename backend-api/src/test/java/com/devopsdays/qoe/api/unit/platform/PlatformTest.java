package com.devopsdays.qoe.api.unit.platform;

import com.devopsdays.qoe.api.models.Platform;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@Tag("unit")
class PlatformTest {

    @ParameterizedTest(name = "fromKey({0}) round-trips")
    @EnumSource(Platform.class)
    void fromKeyRoundTrips(Platform p) {
        Platform resolved = Platform.fromKey(p.getKey());
        assertThat(resolved).isEqualTo(p);
    }

    @ParameterizedTest(name = "fromKey upper/mixed case ''{0}''")
    @ValueSource(strings = {"WEB", "Web", "IPHONE", "Iphone", "ANDROIDPHONE", "Androidphone", "APPLETV", "FireTV", "ANDROIDTV"})
    void fromKeyIsCaseInsensitive(String raw) {
        assertThat(Platform.fromKey(raw)).isNotNull();
    }

    @Test
    void allKeysHasEveryPlatform() {
        assertThat(Platform.allKeys()).hasSize(Platform.values().length);
    }

    @ParameterizedTest(name = "unknown key ''{0}'' throws")
    @ValueSource(strings = {"tvos", "windows_phone", "", "  "})
    void fromKeyThrowsOnUnknown(String raw) {
        assertThatThrownBy(() -> Platform.fromKey(raw))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Unknown platform");
    }

    @Test
    void fromKeyThrowsOnNull() {
        assertThatThrownBy(() -> Platform.fromKey(null))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void tryFromKeyReturnsEmptyForUnknown() {
        assertThat(Platform.tryFromKey("tvos")).isEmpty();
        assertThat(Platform.tryFromKey(null)).isEmpty();
        assertThat(Platform.tryFromKey("")).isEmpty();
    }

    @Test
    void categoryGroupingsAreCorrect() {
        assertThat(Platform.WEB.getCategory()).isEqualTo(Platform.Category.BROWSER);
        assertThat(Platform.IPHONE.getCategory()).isEqualTo(Platform.Category.MOBILE);
        assertThat(Platform.ANDROID_PHONE.getCategory()).isEqualTo(Platform.Category.MOBILE);
        assertThat(Platform.APPLE_TV.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.ANDROID_TV.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.FIRE_TV.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.SAMSUNG_TV.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.LG_TV.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.ROKU.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.CHROMECAST.getCategory()).isEqualTo(Platform.Category.TV);
        assertThat(Platform.XBOX.getCategory()).isEqualTo(Platform.Category.GAMING);
        assertThat(Platform.PLAYSTATION.getCategory()).isEqualTo(Platform.Category.GAMING);
        assertThat(Platform.API.getCategory()).isEqualTo(Platform.Category.INTERNAL);
        assertThat(Platform.AUTOMATION.getCategory()).isEqualTo(Platform.Category.INTERNAL);
    }
}
