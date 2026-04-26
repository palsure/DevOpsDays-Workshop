package com.devopsdays.qoe.api.unit.pipeline;

import com.devopsdays.qoe.api.pipeline.PipelineAcceptanceService;
import com.devopsdays.qoe.api.pipeline.PipelinePlatformResult;
import com.devopsdays.qoe.api.pipeline.PipelinePlatformResultRepository;
import com.devopsdays.qoe.api.pipeline.PipelineRun;
import com.devopsdays.qoe.api.pipeline.PipelineRunRepository;
import com.devopsdays.qoe.api.pipeline.PipelineRunStatus;
import org.junit.jupiter.api.BeforeEach;
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
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@Tag("unit")
@ExtendWith(MockitoExtension.class)
class PipelineAcceptanceServiceTest {

    @Mock
    private PipelineRunRepository pipelineRunRepository;

    @Mock
    private PipelinePlatformResultRepository platformResultRepository;

    private PipelineAcceptanceService service;

    @BeforeEach
    void setUp() {
        service = new PipelineAcceptanceService(pipelineRunRepository, platformResultRepository, 0.8);
    }

    @Test
    void finalizeReleasedWhenPassRateMeetsThreshold() {
        PipelineRun run = PipelineRun.builder()
                .id(1L)
                .runId("run-1")
                .createdAt(Instant.now())
                .status(PipelineRunStatus.PENDING)
                .gateThreshold(0.8)
                .build();

        when(pipelineRunRepository.findByRunId("run-1")).thenReturn(Optional.of(run));
        when(platformResultRepository.findByPipelineRun_Id(1L)).thenReturn(List.of(
                platformRow(run, "api", 8, 2, 0, 10),
                platformRow(run, "web", 9, 1, 0, 10)
        ));
        when(pipelineRunRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        PipelineRun out = service.finalizeRun("run-1");

        // (8+9) / (10+10) = 0.85 >= 0.8
        assertThat(out.getStatus()).isEqualTo(PipelineRunStatus.RELEASED);
        assertThat(out.getOverallPassRate()).isEqualTo(17.0 / 20.0);
    }

    @Test
    void finalizeBlockedBelowThreshold() {
        PipelineRun run = PipelineRun.builder()
                .id(2L)
                .runId("run-2")
                .createdAt(Instant.now())
                .status(PipelineRunStatus.PENDING)
                .gateThreshold(0.8)
                .build();

        when(pipelineRunRepository.findByRunId("run-2")).thenReturn(Optional.of(run));
        when(platformResultRepository.findByPipelineRun_Id(2L)).thenReturn(List.of(
                platformRow(run, "api", 5, 5, 0, 10)
        ));
        when(pipelineRunRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        PipelineRun out = service.finalizeRun("run-2");

        assertThat(out.getStatus()).isEqualTo(PipelineRunStatus.BLOCKED);
        assertThat(out.getOverallPassRate()).isEqualTo(0.5);
    }

    @Test
    void recordPlatformRejectsUnknownName() {
        assertThatThrownBy(() -> service.recordPlatform("run-3", "tvos", 1, 0, 0, 1))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Unknown platform");
    }

    @org.junit.jupiter.params.ParameterizedTest(name = "recordPlatform accepts {0}")
    @org.junit.jupiter.params.provider.ValueSource(strings = {
            "web", "iphone", "ipad", "androidphone", "androidtablet",
            "appletv", "androidtv", "firetv", "samsungtv", "lgtv",
            "roku", "chromecast", "xbox", "playstation",
            "desktop_macos", "desktop_windows", "desktop_linux",
            "api", "automation"
    })
    void recordPlatformAcceptsAllKnownPlatforms(String platformKey) {
        PipelineRun run = PipelineRun.builder()
                .id(99L).runId("run-99").createdAt(Instant.now())
                .status(PipelineRunStatus.PENDING).gateThreshold(0.8).build();

        when(pipelineRunRepository.findByRunId("run-99")).thenReturn(Optional.of(run));
        when(platformResultRepository.findByPipelineRun_IdAndPlatform(99L, platformKey))
                .thenReturn(Optional.empty());
        when(platformResultRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        var result = service.recordPlatform("run-99", platformKey, 9, 1, 0, 10);
        assertThat(result.getPlatform()).isEqualTo(platformKey);
    }

    @Test
    void createRunPersistsThreshold() {
        when(pipelineRunRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        PipelineRun created = service.createRun("gh-99");

        ArgumentCaptor<PipelineRun> cap = ArgumentCaptor.forClass(PipelineRun.class);
        verify(pipelineRunRepository).save(cap.capture());
        assertThat(cap.getValue().getGateThreshold()).isEqualTo(0.8);
        assertThat(cap.getValue().getGithubRunId()).isEqualTo("gh-99");
        assertThat(created.getStatus()).isEqualTo(PipelineRunStatus.PENDING);
    }

    private static PipelinePlatformResult platformRow(
            PipelineRun run, String platform, int p, int f, int s, int t
    ) {
        return PipelinePlatformResult.builder()
                .pipelineRun(run)
                .platform(platform)
                .passed(p)
                .failed(f)
                .skipped(s)
                .total(t)
                .build();
    }
}
