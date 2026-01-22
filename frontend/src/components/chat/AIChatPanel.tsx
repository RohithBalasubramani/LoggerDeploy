import React from 'react';
import { ChevronDown, Check, Send, Bot, User } from 'lucide-react';
import { ChatMessage } from '../../types';
import { SubStepIcon } from '../ui/SubStepIcon';

interface StepConfig {
  title: string;
  steps: string[];
  currentIndex: number;
  isVisible: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  isCompleted: boolean;
  completionMessage: string;
  actions?: { label: string; onClick: () => void }[];
}

interface ActivityItem {
  type: 'ai' | 'human';
  text: string;
}

interface AIChatPanelProps {
  chatInput: string;
  setChatInput: (value: string) => void;
  chatHistory: ChatMessage[];
  isLoading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  stepConfigs: StepConfig[];
  stats: { label: string; value: string }[];
  activeTab: string;
}

// Activity logs for each step showing AI-human collaboration
const STEP_ACTIVITIES: Record<number, ActivityItem[]> = {
  0: [
    { type: 'ai', text: 'Scanning network interfaces...' },
    { type: 'ai', text: 'Found Modbus gateway at 192.168.1.1' },
    { type: 'ai', text: 'Discovered 10 devices behind gateway' },
    { type: 'human', text: 'Confirmed device list' },
    { type: 'ai', text: 'Reading registers from all devices...' },
    { type: 'ai', text: 'Identified 8 MFMs, 1 gateway, 1 router' },
    { type: 'human', text: 'Reviewed device assignments' },
  ],
  1: [
    { type: 'ai', text: 'Analyzing register patterns...' },
    { type: 'ai', text: 'Created "Energy Meter Basic" schema (10 fields)' },
    { type: 'ai', text: 'Created "Energy Meter Advanced" schema (16 fields)' },
    { type: 'human', text: 'Added "Power Quality" schema' },
    { type: 'ai', text: 'Created "Environmental" schema (3 fields)' },
    { type: 'human', text: 'Renamed fields in Three Phase Power' },
  ],
  2: [
    { type: 'ai', text: 'Mapping devices to schemas...' },
    { type: 'ai', text: 'Created 6 table configurations' },
    { type: 'human', text: 'Set poll interval to 5 seconds' },
    { type: 'ai', text: 'Validated 3 tables successfully' },
    { type: 'human', text: 'Reviewing remaining 3 tables...' },
  ],
};

export const AIChatPanel: React.FC<AIChatPanelProps> = ({
  chatInput,
  setChatInput,
  onSubmit,
  stepConfigs,
  activeTab,
}) => {
  const tabToStepIndex: Record<string, number> = {
    'connected devices': 0,
    'schemas': 1,
    'tables': 2,
  };

  const currentStepIndex = tabToStepIndex[activeTab] ?? 0;

  return (
    <div className="w-[380px] bg-white rounded-xl border border-gray-200 flex flex-col shadow-sm flex-none overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <h2 className="font-semibold text-gray-800 text-sm">Setup Progress</h2>
      </div>

      {/* All Steps */}
      <div className="flex-1 overflow-y-auto">
        {stepConfigs.map((step, stepIdx) => {
          const isCurrentStep = stepIdx === currentStepIndex;
          const isPastStep = stepIdx < currentStepIndex;
          const activities = STEP_ACTIVITIES[stepIdx] || [];

          return (
            <div key={stepIdx} className="border-b border-gray-100 last:border-b-0">
              {/* Step Header */}
              <div
                onClick={step.onToggle}
                className={`px-4 py-3 flex items-center justify-between cursor-pointer
                  ${isCurrentStep ? 'bg-gray-50' : 'hover:bg-gray-50'}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold
                    ${step.isCompleted || isPastStep
                      ? 'bg-gray-800 text-white'
                      : isCurrentStep
                        ? 'border-2 border-gray-800 text-gray-800'
                        : 'border border-gray-300 text-gray-400'}`}
                  >
                    {step.isCompleted || isPastStep ? <Check className="w-3 h-3 stroke-[3px]" /> : stepIdx + 1}
                  </div>
                  <div>
                    <span className={`text-sm font-medium ${isCurrentStep ? 'text-gray-900' : 'text-gray-600'}`}>
                      {step.title}
                    </span>
                    {(step.isCompleted || isPastStep) && !isCurrentStep && (
                      <span className="text-xs text-gray-400 ml-2">Done</span>
                    )}
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200
                  ${step.isExpanded || isCurrentStep ? '' : '-rotate-90'}`}
                />
              </div>

              {/* Step Content - expanded for current step or if manually expanded */}
              {(step.isExpanded || isCurrentStep) && (
                <div className="px-4 pb-3">
                  {/* Sub-steps */}
                  <div className="pl-3 mb-3">
                    <div className="relative pl-4">
                      <div className="absolute left-[3px] top-1 bottom-1 w-px border-l border-dashed border-gray-200" />
                      {step.steps.map((label, idx) => (
                        <div key={idx} className="flex items-center gap-2 py-1 relative">
                          <SubStepIcon index={idx} currentIndex={step.currentIndex} />
                          <span className={`text-xs ${idx <= step.currentIndex ? 'text-gray-700' : 'text-gray-400'}`}>
                            {label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Activity Log */}
                  <div className="space-y-1.5 pt-2 border-t border-gray-100">
                    {activities.map((activity, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <div className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 mt-0.5
                          ${activity.type === 'ai' ? 'bg-gray-100' : 'bg-gray-800'}`}>
                          {activity.type === 'ai'
                            ? <Bot className="w-2.5 h-2.5 text-gray-500" />
                            : <User className="w-2.5 h-2.5 text-white" />
                          }
                        </div>
                        <span className={`text-xs leading-relaxed
                          ${activity.type === 'ai' ? 'text-gray-500' : 'text-gray-700 font-medium'}`}>
                          {activity.text}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Action button for current step */}
                  {isCurrentStep && step.actions && step.actions.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      {step.actions.map((action, i) => (
                        <button
                          key={i}
                          onClick={action.onClick}
                          className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                        >
                          {action.label} →
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-100">
        <form onSubmit={onSubmit} className="relative">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask a question..."
            className="w-full bg-gray-50 border border-gray-200 rounded-lg py-2 pl-3 pr-10 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-gray-300"
          />
          <button
            type="submit"
            disabled={!chatInput.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 disabled:text-gray-300"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
