import React, { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  FiChevronLeft,
  FiChevronRight,
  FiGrid,
  FiMonitor,
  FiPlay,
  FiPlus,
  FiRefreshCw,
  FiTrash2,
} from "react-icons/fi";

import DataChart from "./DataChart";


function SlidePreview({
  slides,
  currentSlide,
  onNavigate,
  onSlideChange,
  quiz,
  onStartSlideshow,
  onRegenerateSlide,
  regeneratingSlideIndex,
  loading,
  viewMode,
  onViewModeChange,
}) {
  const [quizSelections, setQuizSelections] = useState({});

  useEffect(() => {
    setQuizSelections({});
  }, [quiz]);

  if (loading && !slides.length) {
    return (
      <section className="panel preview-empty">
        <div className="loading-state">
          <span className="spinner-inline" />
          <h2>Generating your slide deck...</h2>
          <p className="muted-copy">The workspace will update as soon as the backend returns the deck.</p>
        </div>
      </section>
    );
  }

  if (!slides.length) {
    return (
      <section className="panel preview-empty">
        <div className="loading-state">
          <h2>No slides generated yet</h2>
          <p className="muted-copy">
            Submit notes or upload a PDF/TXT file to unlock the editable slide workspace and quiz preview.
          </p>
        </div>
      </section>
    );
  }

  const slide = slides[currentSlide];
  const slideTypeLabel =
    slide.type === "data" ? "Data Insight" : slide.type === "explanation" ? "Explained Simply" : "Core Slide";
  const isRegenerating = regeneratingSlideIndex === currentSlide;

  const updateSlide = (updatedSlide) => {
    onSlideChange(currentSlide, updatedSlide);
  };

  const updatePoint = (pointIndex, value) => {
    const nextPoints = slide.points.map((point, index) => (index === pointIndex ? value : point));
    updateSlide({ ...slide, points: nextPoints });
  };

  const addPoint = () => {
    updateSlide({ ...slide, points: [...slide.points, "New teaching point"] });
  };

  const removePoint = (pointIndex) => {
    updateSlide({
      ...slide,
      points: slide.points.filter((_, index) => index !== pointIndex),
    });
  };

  const handleQuizSelect = (questionIndex, option) => {
    setQuizSelections((currentSelections) => {
      if (currentSelections[questionIndex]?.showAnswer) {
        return currentSelections;
      }

      return {
        ...currentSelections,
        [questionIndex]: {
          selected: option,
          showAnswer: true,
        },
      };
    });
  };

  const getOptionState = (questionIndex, option, answer) => {
    const selection = quizSelections[questionIndex];
    if (!selection?.showAnswer) {
      return "";
    }
    if (option === answer) {
      return "correct";
    }
    if (selection.selected === option) {
      return "incorrect";
    }
    return "revealed";
  };

  return (
    <motion.section
      className="panel workspace-panel"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: "easeOut", delay: 0.08 }}
    >
      <div className="workspace-header">
        <div>
          <p className="eyebrow">Preview Workspace</p>
          <h2>Focus on one slide without the clutter</h2>
          <p className="panel-copy">
            Jump across slides with compact tabs, switch to overview mode when needed, then fine-tune the
            active slide inline.
          </p>
        </div>

        <div className="workspace-actions">
          <div className="view-toggle">
            <button
              type="button"
              className={`view-toggle-button ${viewMode === "single" ? "active" : ""}`}
              onClick={() => onViewModeChange("single")}
            >
              <FiMonitor />
              Single
            </button>
            <button
              type="button"
              className={`view-toggle-button ${viewMode === "grid" ? "active" : ""}`}
              onClick={() => onViewModeChange("grid")}
            >
              <FiGrid />
              Grid
            </button>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={() => onStartSlideshow(currentSlide)}
          >
            <FiPlay />
            Start Slideshow
          </button>
        </div>
      </div>

      <div className="tab-rail" role="tablist" aria-label="Slides">
        {slides.map((item, index) => (
          <button
            key={`${item.title}-${index}`}
            type="button"
            className={`slide-tab ${index === currentSlide ? "active" : ""}`}
            title={item.title}
            onClick={() => {
              onNavigate(index);
              onViewModeChange("single");
            }}
          >
            <span className="slide-tab-index">{index + 1}</span>
            <span className="slide-tab-label">{item.title || `Slide ${index + 1}`}</span>
          </button>
        ))}
      </div>

      {viewMode === "grid" ? (
        <motion.div
          className="slide-grid"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >
          {slides.map((item, index) => {
            const cardTypeLabel =
              item.type === "data"
                ? "Data Insight"
                : item.type === "explanation"
                  ? "Explained Simply"
                  : "Core Slide";

            return (
              <button
                key={`${item.title}-${index}-grid`}
                type="button"
                className={`grid-slide-card ${index === currentSlide ? "active" : ""}`}
                onClick={() => {
                  onNavigate(index);
                  onViewModeChange("single");
                }}
              >
                <div className="grid-slide-top">
                  <span className={`badge slide-type-badge ${item.type || "normal"}`}>{cardTypeLabel}</span>
                  <span className="grid-slide-counter">{index + 1}</span>
                </div>

                <h3>{item.title}</h3>

                <ul className="grid-slide-points">
                  {item.points.slice(0, 3).map((point, pointIndex) => (
                    <li key={`${point}-${pointIndex}`}>{point}</li>
                  ))}
                </ul>

                <span className="grid-slide-link">Open slide</span>
              </button>
            );
          })}
        </motion.div>
      ) : (
        <div className="focus-stage">
          <div className="slide-toolbar">
            <div className="slide-meta-stack">
              <span className={`badge slide-type-badge ${slide.type || "normal"}`}>{slideTypeLabel}</span>
              {slide.extra_explanation ? <span className="status-pill ready">Extra explanation</span> : null}
            </div>

            <div className="preview-inline-actions">
              <span className="muted-inline">Editing slide {currentSlide + 1}</span>
              <button
                type="button"
                className="secondary-button"
                onClick={() => onRegenerateSlide(currentSlide)}
                disabled={isRegenerating}
              >
                <FiRefreshCw />
                {isRegenerating ? "Regenerating..." : "Regenerate"}
              </button>
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.article
              key={`${slide.title}-${currentSlide}`}
              className="slide-canvas"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.985 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
            >
              <span className="slide-card-kicker">Lesson Slide {currentSlide + 1}</span>

              <input
                className="slide-title-input"
                value={slide.title}
                onChange={(event) => updateSlide({ ...slide, title: event.target.value })}
              />

              <div className="points-editor">
                {slide.points.map((point, index) => (
                  <div key={`${index}-${slide.title}`} className="point-row">
                    <span className="bullet-marker">{String(index + 1).padStart(2, "0")}</span>
                    <textarea
                      className="point-input"
                      value={point}
                      rows={2}
                      onChange={(event) => updatePoint(index, event.target.value)}
                    />
                    <button
                      type="button"
                      className="icon-button ghost"
                      aria-label={`Remove bullet ${index + 1}`}
                      onClick={() => removePoint(index)}
                      disabled={slide.points.length <= 1}
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                ))}
              </div>

              <div className="slide-footer-actions">
                <button type="button" className="secondary-button" onClick={addPoint}>
                  <FiPlus />
                  Add bullet
                </button>
              </div>

              {slide.type === "data" && slide.chart_data?.length ? <DataChart chartData={slide.chart_data} /> : null}
            </motion.article>
          </AnimatePresence>

          <div className="slide-nav-footer">
            <button
              type="button"
              className="secondary-button nav-button"
              onClick={() => onNavigate(currentSlide - 1)}
              disabled={currentSlide === 0}
            >
              <FiChevronLeft />
              Previous
            </button>

            <div className="slide-counter-card">
              <span className="slide-counter-label">Current View</span>
              <strong>
                Slide {currentSlide + 1} of {slides.length}
              </strong>
            </div>

            <button
              type="button"
              className="primary-button nav-button"
              onClick={() => onNavigate(currentSlide + 1)}
              disabled={currentSlide === slides.length - 1}
            >
              Next
              <FiChevronRight />
            </button>
          </div>
        </div>
      )}

      <div className="quiz-block">
        <div className="panel-header compact">
          <div>
            <p className="eyebrow">Quiz Generator</p>
            <h3>Interactive practice mode</h3>
          </div>
        </div>

        {quiz.length ? (
          <div className="quiz-grid">
            {quiz.map((item, index) => (
              <article key={`${item.question}-${index}`} className="quiz-card">
                <span className="quiz-index">Q{index + 1}</span>
                <h4>{item.question}</h4>

                <div className="quiz-options">
                  {item.options.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`quiz-option-button ${getOptionState(index, option, item.answer)}`}
                      onClick={() => handleQuizSelect(index, option)}
                      disabled={Boolean(quizSelections[index]?.showAnswer)}
                    >
                      <span>{option}</span>
                    </button>
                  ))}
                </div>

                {quizSelections[index]?.showAnswer ? (
                  <p
                    className={`quiz-feedback ${
                      quizSelections[index].selected === item.answer ? "correct" : "incorrect"
                    }`}
                  >
                    {quizSelections[index].selected === item.answer ? "Correct ✅" : "Wrong ❌"}
                  </p>
                ) : (
                  <p className="quiz-prompt">Choose an answer to reveal feedback.</p>
                )}
              </article>
            ))}
          </div>
        ) : (
          <p className="muted-copy">Quiz questions will appear here after slide generation completes.</p>
        )}
      </div>
    </motion.section>
  );
}

export default SlidePreview;
