import React from 'react';
import { Check } from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  tabs: string[];
  isTabClickable: (tab: string) => boolean;
  completedSteps: boolean[];
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  tabs,
  isTabClickable,
  completedSteps
}) => {
  return (
    <div className="h-20 bg-white rounded-xl border border-gray-200 flex flex-col px-8 shadow-sm">
      <div className="mt-auto flex items-center gap-8 h-10 pb-1">
        {tabs.map((label, i) => {
          const clickable = isTabClickable(label);
          const isActive = activeTab === label.toLowerCase();
          const isCompleted = completedSteps[i];

          return (
            <React.Fragment key={label}>
              <button
                onClick={() => clickable && setActiveTab(label.toLowerCase())}
                disabled={!clickable}
                className={`flex items-center gap-2 transition-all h-full outline-none focus:outline-none
                  ${isActive ? 'text-gray-900' : clickable ? 'text-gray-400 hover:text-gray-600' : 'text-gray-300 cursor-not-allowed'}`}
              >
                <span className={`flex items-center justify-center w-5 h-5 rounded-full text-xs font-semibold transition-all
                  ${isCompleted
                    ? 'bg-emerald-500 text-white border-0'
                    : isActive
                      ? 'border-2 border-emerald-500 text-emerald-600 bg-white'
                      : clickable
                        ? 'border border-gray-300 text-gray-400'
                        : 'border border-gray-200 text-gray-300'
                  }`}>
                  {isCompleted ? <Check className="w-3 h-3 stroke-[3px]" /> : i + 1}
                </span>
                <span className={`font-medium text-sm ${isActive ? 'font-semibold' : ''}`}>{label}</span>
              </button>
              {i < tabs.length - 1 && (
                <div className={`w-16 border-b border-dashed ${isCompleted ? 'border-emerald-400' : clickable ? 'border-gray-300' : 'border-gray-200'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
