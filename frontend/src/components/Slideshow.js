import React, { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FiChevronLeft, FiChevronRight, FiPause, FiPlay, FiX } from "react-icons/fi";

function Slideshow({ slides, initialIndex = 0, onClose, quizCount = 0 }) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [autoplay, setAutoplay] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const maxIndex = Math.max(slides.length - 1, 0);
    setCurrentIndex(Math.min(Math.max(initialIndex, 0), maxIndex));
  }, [initialIndex, slides.length]);

  useEffect(() => {
    document.body.style.overflow = "hidden";

    const node = containerRef.current;
    if (node?.requestFullscreen) {
      const fullscreenAttempt = node.requestFullscreen();
      if (fullscreenAttempt?.catch) {
        fullscreenAttempt.catch(() => {});
      }
    }

    return () => {
      document.body.style.overflow = "";
      if (document.fullscreenElement === node && document.exitFullscreen) {
        const exitAttempt = document.exitFullscreen();
        if (exitAttempt?.catch) {
          exitAttempt.catch(() => {});
        }
      }
    };
  }, []);

  useEffect(() => {
    if (!autoplay || !slides.length) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setCurrentIndex((index) => {
        if (index >= slides.length - 1) {
          window.clearInterval(timer);
          setAutoplay(false);
          return index;
        }
        return index + 1;
      });
    }, 3000);

    return () => window.clearInterval(timer);
  }, [autoplay, slides.length]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "ArrowRight") {
        event.preventDefault();
        setCurrentIndex((index) => Math.min(index + 1, slides.length - 1));
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setCurrentIndex((index) => Math.max(index - 1, 0));
      }

      if (event.key === "Escape") {
        event.preventDefault();
        onClose(currentIndex);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, onClose, slides.length]);

  if (!slides.length) {
    return null;
  }

  const slide = slides[currentIndex];
  const progress = ((currentIndex + 1) / slides.length) * 100;

  return (
    <div className="slideshow-overlay" ref={containerRef}>
      <div className="slideshow-shell">
        <div className="slideshow-topbar">
          <span className="slideshow-counter">
            Slide {currentIndex + 1} / {slides.length}
          </span>

          <div className="slideshow-toolbar">
            <button type="button" className="secondary-button" onClick={() => setAutoplay((value) => !value)}>
              {autoplay ? <FiPause /> : <FiPlay />}
              {autoplay ? "Stop Auto-play" : "Auto-play"}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => setCurrentIndex((index) => Math.max(index - 1, 0))}
              disabled={currentIndex === 0}
            >
              <FiChevronLeft />
              Previous
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={() => setCurrentIndex((index) => Math.min(index + 1, slides.length - 1))}
              disabled={currentIndex === slides.length - 1}
            >
              Next
              <FiChevronRight />
            </button>

            <button type="button" className="secondary-button" onClick={() => onClose(currentIndex)}>
              <FiX />
              Exit
            </button>
          </div>
        </div>

        <div className="slideshow-progress" aria-hidden="true">
          <div className="slideshow-progress-fill" style={{ width: `${progress}%` }} />
        </div>

        <AnimatePresence mode="wait">
          <motion.article
            key={`${slide.title}-${currentIndex}`}
            className="slideshow-stage"
            initial={{ opacity: 0, y: 22, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -14, scale: 0.985 }}
            transition={{ duration: 0.26, ease: "easeOut" }}
          >
            <div className="slideshow-stage-header">
              <span className="badge">Presentation mode</span>
              <span className="muted-inline">
                {autoplay ? "Auto-play every 3 seconds" : "Use left and right arrow keys to navigate"}
              </span>
            </div>

            <h2 className="slideshow-title">{slide.title}</h2>

            <div className="slideshow-divider" />

            <ul className="slideshow-points">
              {slide.points.map((point, index) => (
                <li key={`${index}-${point}`} className="slideshow-point">
                  <span className="slideshow-point-marker">{index + 1}</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </motion.article>
        </AnimatePresence>

        <p className="slideshow-hint">
          Full-screen slideshow is active. Press Esc to close.
          {quizCount ? ` ${quizCount} quiz questions are ready after the deck.` : ""}
        </p>
      </div>
    </div>
  );
}

export default Slideshow;
