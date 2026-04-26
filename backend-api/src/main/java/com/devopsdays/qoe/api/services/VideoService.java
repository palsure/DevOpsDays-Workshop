package com.devopsdays.qoe.api.services;

import com.devopsdays.qoe.api.models.Video;
import com.devopsdays.qoe.api.repositories.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class VideoService {

    private final VideoRepository repository;

    public List<Video> getAllVideos() {
        return repository.findAll();
    }

    public Optional<Video> getVideoById(String videoId) {
        return repository.findByVideoId(videoId);
    }

    @Transactional
    public Video createVideo(Map<String, Object> videoData) {
        Video video = Video.builder()
                .videoId((String) videoData.get("videoId"))
                .title((String) videoData.get("title"))
                .description((String) videoData.get("description"))
                .thumbnailUrl((String) videoData.get("thumbnailUrl"))
                .hlsManifestUrl((String) videoData.get("hlsManifestUrl"))
                .dashManifestUrl((String) videoData.get("dashManifestUrl"))
                .duration(videoData.get("duration") != null ? ((Number) videoData.get("duration")).longValue() : null)
                .resolution((String) videoData.get("resolution"))
                .bitrate(videoData.get("bitrate") != null ? ((Number) videoData.get("bitrate")).longValue() : null)
                .build();

        Video saved = repository.save(video);
        log.info("Created video: videoId={}, title={}", saved.getVideoId(), saved.getTitle());
        return saved;
    }
}
