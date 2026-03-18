import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";
import { Bar } from "react-chartjs-2";


ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function DataChart({ chartData }) {
  const safeChartData =
    chartData?.length
      ? chartData
      : [
          { label: "Metric A", value: 12, unit: "" },
          { label: "Metric B", value: 19, unit: "" },
          { label: "Metric C", value: 7, unit: "" },
        ];

  const labels = safeChartData.map((item) => item.label);
  const values = safeChartData.map((item) => item.value);
  const units = safeChartData.map((item) => item.unit || "");

  const data = {
    labels,
    datasets: [
      {
        label: "Detected values",
        data: values,
        backgroundColor: "rgba(14, 165, 233, 0.55)",
        borderColor: "rgba(15, 118, 110, 0.95)",
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: "Data Insights",
        color: "#0f172a",
        font: {
          size: 16,
          weight: "700",
        },
      },
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const unit = units[context.dataIndex] || "";
            return `${context.dataset.label}: ${context.parsed.y}${unit}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          color: "#475569",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.16)",
        },
      },
      x: {
        ticks: {
          color: "#475569",
        },
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div className="chart-wrapper">
      <div className="chart-header">
        <span className="badge">Auto visual</span>
        <span className="muted-inline">Bar view</span>
      </div>
      <div className="chart-surface">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}

export default DataChart;
