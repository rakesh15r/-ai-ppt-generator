import React from "react";
import { motion } from "framer-motion";
import { FiBookOpen, FiLayers, FiSliders } from "react-icons/fi";

function SettingsPanel({ settings, onChange }) {
  const densityOptions = [
    { value: "concise", label: "Concise", meta: "Keep slides lean with roughly 3 bullets." },
    { value: "detailed", label: "Detailed", meta: "Allow fuller teaching notes with 5 to 7 bullets." },
  ];

  const difficultyOptions = ["Beginner", "Intermediate", "Advanced"];

  return (
    <motion.section
      className="panel"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: 0.05 }}
    >
      <div className="panel-header">
        <div>
          <p className="eyebrow">Presentation Controls</p>
          <h2>Shape the deck before generation</h2>
          <p className="panel-copy">
            Choose explanation depth, how dense each slide should be, and how many slides you want.
          </p>
        </div>
      </div>

      <div className="settings-grid">
        <div className="setting-group">
          <div className="setting-heading">
            <label className="setting-label">
              <FiLayers />
              Number of Slides
            </label>
            <span className="setting-value">{settings.slideCount}</span>
          </div>

          <input
            type="range"
            min="5"
            max="15"
            step="1"
            value={settings.slideCount}
            className="range-slider"
            onChange={(event) =>
              onChange({ ...settings, slideCount: Number(event.target.value) })
            }
          />

          <div className="range-labels">
            <span>5 slides</span>
            <span>15 slides</span>
          </div>
        </div>

        <div className="setting-group">
          <label className="setting-label">
            <FiSliders />
            Slide density
          </label>

          <div className="density-toggle">
            {densityOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`density-button ${settings.density === option.value ? "active" : ""}`}
                onClick={() => onChange({ ...settings, density: option.value })}
              >
                <span>{option.label}</span>
                <small className="density-copy">{option.meta}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="setting-group">
          <label className="setting-label" htmlFor="difficulty-select">
            <FiBookOpen />
            Difficulty level
          </label>

          <select
            id="difficulty-select"
            className="difficulty-select"
            value={settings.difficulty}
            onChange={(event) => onChange({ ...settings, difficulty: event.target.value })}
          >
            {difficultyOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      </div>
    </motion.section>
  );
}

export default SettingsPanel;
