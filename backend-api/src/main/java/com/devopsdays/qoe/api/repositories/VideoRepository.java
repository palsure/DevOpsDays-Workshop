package com.devopsdays.qoe.api.repositories;

import com.devopsdays.qoe.api.models.Video;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface VideoRepository extends JpaRepository<Video, Long> {
    Optional<Video> findByVideoId(String videoId);
}
