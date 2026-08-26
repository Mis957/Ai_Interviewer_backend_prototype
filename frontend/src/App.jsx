import React, { useState } from 'react';
import Navbar from './components/Navbar';
import TechnologySelector from './components/TechnologySelector';
import InterviewStudio from './components/InterviewStudio';
import EvaluationModal from './components/EvaluationModal';
import PerformanceReport from './components/PerformanceReport';
import LearnedInsights from './components/LearnedInsights';
import { startInterview, submitAnswer, endInterview } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('studio'); // studio | insights
  const [step, setStep] = useState('select'); // select | interview | report
  
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionCount, setQuestionCount] = useState(1);
  const [evaluation, setEvaluation] = useState(null);
  const [finalReport, setFinalReport] = useState(null);
  
  const [isLoading, setIsLoading] = useState(false);

  // 1. Start Interview Flow
  const handleStartInterview = async (technology, initialDifficulty) => {
    setIsLoading(true);
    try {
      const data = await startInterview(technology, initialDifficulty);
      setSession(data);
      setCurrentQuestion(data.first_question);
      setQuestionCount(1);
      setStep('interview');
    } catch (err) {
      alert(`Error starting interview session: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Submit Answer Flow
  const handleSubmitAnswer = async ({ candidateAnswer, audioBlob }) => {
    setIsLoading(true);
    try {
      const data = await submitAnswer({
        sessionId: session.session_id,
        questionId: currentQuestion.question_id,
        generatedQuestionId: currentQuestion.generated_question_id,
        candidateAnswer,
        audioBlob
      });
      setEvaluation(data);
    } catch (err) {
      alert(`Error submitting answer: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Proceed to Next Question or Final Report
  const handleNextQuestion = async () => {
    if (evaluation?.session_completed || !evaluation?.next_question) {
      // Session finished, fetch final report
      handleEndInterview();
    } else {
      setCurrentQuestion(evaluation.next_question);
      setQuestionCount((prev) => prev + 1);
      setEvaluation(null);
    }
  };

  // 4. End Interview Flow
  const handleEndInterview = async () => {
    if (!session) return;
    setIsLoading(true);
    try {
      const report = await endInterview(session.session_id);
      setFinalReport(report);
      setEvaluation(null);
      setStep('report');
    } catch (err) {
      alert(`Error concluding interview: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 5. Restart Session Flow
  const handleRestart = () => {
    setSession(null);
    setCurrentQuestion(null);
    setQuestionCount(1);
    setEvaluation(null);
    setFinalReport(null);
    setStep('select');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main style={{ flex: 1, paddingBottom: '3rem' }}>
        {activeTab === 'insights' ? (
          <LearnedInsights />
        ) : (
          <>
            {step === 'select' && (
              <TechnologySelector onStartInterview={handleStartInterview} isLoading={isLoading} />
            )}

            {step === 'interview' && currentQuestion && (
              <InterviewStudio
                session={session}
                currentQuestion={currentQuestion}
                onSubmitAnswer={handleSubmitAnswer}
                onEndInterview={handleEndInterview}
                isLoading={isLoading}
                questionNumber={questionCount}
              />
            )}

            {step === 'report' && finalReport && (
              <PerformanceReport report={finalReport} onRestart={handleRestart} />
            )}
          </>
        )}
      </main>

      {/* Evaluation Feedback Modal */}
      {evaluation && (
        <EvaluationModal
          evaluation={evaluation}
          onNextQuestion={handleNextQuestion}
          isCompleted={evaluation.session_completed}
        />
      )}
    </div>
  );
}
