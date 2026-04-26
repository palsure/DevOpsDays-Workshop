package com.devopsdays.qoe.api.controllers;

import com.devopsdays.qoe.api.models.Video;
import com.devopsdays.qoe.api.services.VideoService;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/videos")
@RequiredArgsConstructor
@Tag(name = "Videos", description = "Catalog and manifest URLs for demo streams")
public class VideoController {

    private final VideoService videoService;

    @GetMapping
    public ResponseEntity<List<Video>> listVideos() {
        List<Video> videos = videoService.getAllVideos();
        return ResponseEntity.ok(videos);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Video> getVideo(@PathVariable String id) {
        return videoService.getVideoById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/manifest")
    public ResponseEntity<Map<String, String>> getManifest(@PathVariable String id) {
        return videoService.getVideoById(id)
                .map(video -> {
                    Map<String, String> manifest = Map.of(
                            "hls", video.getHlsManifestUrl() != null ? video.getHlsManifestUrl() : "",
                            "dash", video.getDashManifestUrl() != null ? video.getDashManifestUrl() : ""
                    );
                    return ResponseEntity.ok(manifest);
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<Video> createVideo(@Valid @RequestBody Map<String, Object> videoData) {
        Video video = videoService.createVideo(videoData);
        return ResponseEntity.status(HttpStatus.CREATED).body(video);
    }
}
