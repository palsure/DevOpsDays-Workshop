package com.devopsdays.qoe.api.unit.video;

import com.devopsdays.qoe.api.exceptions.VideoNotFoundException;
import com.devopsdays.qoe.api.models.Video;
import com.devopsdays.qoe.api.models.VideoRequest;
import com.devopsdays.qoe.api.repositories.VideoRepository;
import com.devopsdays.qoe.api.services.VideoService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@Tag("unit")
@ExtendWith(MockitoExtension.class)
@DisplayName("VideoService")
class VideoServiceTest {

    @Mock
    private VideoRepository repository;

    private VideoService service;

    @BeforeEach
    void setUp() {
        service = new VideoService(repository);
    }

    // ─── helpers ──────────────────────────────────────────────────────────────

    private static Video activeVideo(String videoId, String title, String category) {
        return Video.builder()
                .id(1L)
                .videoId(videoId)
                .title(title)
                .description("Test description")
                .category(category)
                .genre("animation")
                .active(true)
                .hlsManifestUrl("https://example.com/" + videoId + ".m3u8")
                .dashManifestUrl("https://example.com/" + videoId + ".mpd")
                .duration(600L)
                .resolution("1920x1080")
                .bitrate(5000000L)
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();
    }

    private static VideoRequest sampleRequest(String videoId) {
        return new VideoRequest(
                videoId, "Test Title", "Test description",
                "https://example.com/thumb.jpg",
                "https://example.com/video.m3u8",
                "https://example.com/video.mpd",
                600L, "1920x1080", 5000000L, "movie", "drama"
        );
    }

    // ─── getAllVideos ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("getAllVideos")
    class GetAllVideos {

        @Test
        @DisplayName("returns only active videos from repository")
        void returnsActiveVideos() {
            List<Video> expected = List.of(
                    activeVideo("v1", "Video 1", "movie"),
                    activeVideo("v2", "Video 2", "show")
            );
            when(repository.findByActiveTrue()).thenReturn(expected);

            List<Video> result = service.getAllVideos();

            assertThat(result).hasSize(2).isEqualTo(expected);
            verify(repository).findByActiveTrue();
        }

        @Test
        @DisplayName("returns empty list when no active videos exist")
        void returnsEmptyList() {
            when(repository.findByActiveTrue()).thenReturn(List.of());

            assertThat(service.getAllVideos()).isEmpty();
        }
    }

    // ─── getVideoById ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("getVideoById")
    class GetVideoById {

        @Test
        @DisplayName("returns video when found and active")
        void returnsVideoWhenFoundAndActive() {
            Video video = activeVideo("vid-001", "Big Buck Bunny", "movie");
            when(repository.findByVideoId("vid-001")).thenReturn(Optional.of(video));

            Optional<Video> result = service.getVideoById("vid-001");

            assertThat(result).isPresent().contains(video);
        }

        @Test
        @DisplayName("returns empty when video is soft-deleted")
        void returnsEmptyForInactiveVideo() {
            Video inactive = activeVideo("vid-002", "Deleted Video", "movie");
            inactive.setActive(false);
            when(repository.findByVideoId("vid-002")).thenReturn(Optional.of(inactive));

            assertThat(service.getVideoById("vid-002")).isEmpty();
        }

        @Test
        @DisplayName("returns empty when video does not exist")
        void returnsEmptyWhenNotFound() {
            when(repository.findByVideoId("missing")).thenReturn(Optional.empty());

            assertThat(service.getVideoById("missing")).isEmpty();
        }
    }

    // ─── searchVideos ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("searchVideos")
    class SearchVideos {

        @Test
        @DisplayName("delegates to repository.search with trimmed query")
        void delegatesToRepository() {
            List<Video> results = List.of(activeVideo("vid-001", "Big Buck Bunny", "movie"));
            when(repository.search("bunny")).thenReturn(results);

            List<Video> actual = service.searchVideos("  bunny  ");

            assertThat(actual).isEqualTo(results);
            verify(repository).search("bunny");
        }

        @Test
        @DisplayName("returns all active videos when query is blank")
        void returnsAllWhenBlankQuery() {
            List<Video> all = List.of(activeVideo("v1", "Title", "movie"));
            when(repository.findByActiveTrue()).thenReturn(all);

            assertThat(service.searchVideos("   ")).isEqualTo(all);
            verify(repository, never()).search(anyString());
        }

        @Test
        @DisplayName("returns all active videos when query is null")
        void returnsAllWhenNullQuery() {
            when(repository.findByActiveTrue()).thenReturn(List.of());

            service.searchVideos(null);

            verify(repository).findByActiveTrue();
            verify(repository, never()).search(anyString());
        }
    }

    // ─── getByCategory ────────────────────────────────────────────────────────

    @Nested
    @DisplayName("getByCategory")
    class GetByCategory {

        @Test
        @DisplayName("delegates to repository with the category string")
        void delegatesToRepository() {
            List<Video> movies = List.of(activeVideo("vid-001", "Sintel", "movie"));
            when(repository.findByCategoryIgnoreCaseAndActiveTrue("movie")).thenReturn(movies);

            List<Video> result = service.getByCategory("movie");

            assertThat(result).isEqualTo(movies);
        }
    }

    // ─── createVideo ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("createVideo")
    class CreateVideo {

        @Test
        @DisplayName("persists a new video and returns the saved entity")
        void persistsVideo() {
            VideoRequest req = sampleRequest("new-vid-001");
            when(repository.existsByVideoId("new-vid-001")).thenReturn(false);
            when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

            Video saved = service.createVideo(req);

            assertThat(saved.getVideoId()).isEqualTo("new-vid-001");
            assertThat(saved.getTitle()).isEqualTo("Test Title");
            assertThat(saved.getCategory()).isEqualTo("movie");
            assertThat(saved.getGenre()).isEqualTo("drama");
            assertThat(saved.getActive()).isTrue();

            ArgumentCaptor<Video> cap = ArgumentCaptor.forClass(Video.class);
            verify(repository).save(cap.capture());
            assertThat(cap.getValue().getDuration()).isEqualTo(600L);
        }

        @Test
        @DisplayName("throws IllegalArgumentException when videoId already exists")
        void throwsWhenDuplicate() {
            when(repository.existsByVideoId("dup-vid")).thenReturn(true);

            assertThatThrownBy(() -> service.createVideo(sampleRequest("dup-vid")))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("dup-vid");

            verify(repository, never()).save(any());
        }
    }

    // ─── updateVideo ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("updateVideo")
    class UpdateVideo {

        @Test
        @DisplayName("updates all mutable fields and returns saved entity")
        void updatesAllFields() {
            Video existing = activeVideo("vid-update", "Old Title", "show");
            when(repository.findByVideoId("vid-update")).thenReturn(Optional.of(existing));
            when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

            VideoRequest req = new VideoRequest(
                    "vid-update", "New Title", "New desc",
                    "https://example.com/new-thumb.jpg",
                    "https://example.com/new.m3u8",
                    "https://example.com/new.mpd",
                    900L, "3840x2160", 12000000L, "documentary", "nature"
            );

            Video result = service.updateVideo("vid-update", req);

            assertThat(result.getTitle()).isEqualTo("New Title");
            assertThat(result.getCategory()).isEqualTo("documentary");
            assertThat(result.getDuration()).isEqualTo(900L);
        }

        @Test
        @DisplayName("throws VideoNotFoundException when video does not exist")
        void throwsWhenNotFound() {
            when(repository.findByVideoId("ghost")).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.updateVideo("ghost", sampleRequest("ghost")))
                    .isInstanceOf(VideoNotFoundException.class)
                    .hasMessageContaining("ghost");
        }
    }

    // ─── deleteVideo ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("deleteVideo")
    class DeleteVideo {

        @Test
        @DisplayName("sets active=false and saves the entity")
        void setsActiveFalse() {
            Video video = activeVideo("vid-del", "To Delete", "movie");
            when(repository.findByVideoId("vid-del")).thenReturn(Optional.of(video));
            when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

            service.deleteVideo("vid-del");

            ArgumentCaptor<Video> cap = ArgumentCaptor.forClass(Video.class);
            verify(repository).save(cap.capture());
            assertThat(cap.getValue().getActive()).isFalse();
        }

        @Test
        @DisplayName("throws VideoNotFoundException when video does not exist")
        void throwsWhenNotFound() {
            when(repository.findByVideoId("gone")).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.deleteVideo("gone"))
                    .isInstanceOf(VideoNotFoundException.class)
                    .hasMessageContaining("gone");
        }
    }
}
