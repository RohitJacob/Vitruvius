import { useRef, useEffect, useState } from "react";
import { useReportStore } from "./stores/reportStore";
import Layout from "./components/Layout";
import UploadPanel from "./components/UploadPanel";
import ProcessingPanel from "./components/ProcessingPanel";
import ReviewPanel from "./components/ReviewPanel";
import GeneratePanel from "./components/GeneratePanel";
import type { AppStep } from "./types";

const panels: Record<AppStep, () => JSX.Element> = {
  upload: UploadPanel,
  processing: ProcessingPanel,
  review: ReviewPanel,
  generate: GeneratePanel,
};

export default function App() {
  const step = useReportStore((s) => s.step);
  const [visible, setVisible] = useState(true);
  const [displayStep, setDisplayStep] = useState<AppStep>(step);
  const prevStep = useRef(step);

  useEffect(() => {
    if (step !== prevStep.current) {
      setVisible(false);
      const timeout = setTimeout(() => {
        setDisplayStep(step);
        setVisible(true);
        prevStep.current = step;
      }, 250);
      return () => clearTimeout(timeout);
    }
  }, [step]);

  const Panel = panels[displayStep];

  return (
    <Layout>
      <div
        className={`transition-all duration-300 ease-out ${
          visible
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-2"
        }`}
      >
        <Panel />
      </div>
    </Layout>
  );
}
