import React from 'react';
import { Check, Loader2 } from 'lucide-react';

interface SubStepIconProps {
  index: number;
  currentIndex: number;
}

export const SubStepIcon: React.FC<SubStepIconProps> = ({ index, currentIndex }) => {
  const isCompleted = index < currentIndex;
  const isActive = index === currentIndex;

  return (
    <div
      className="flex items-center justify-center w-[2.2vh] h-[2.2vh] flex-none bg-white rounded-full border border-gray-200 z-10 shadow-sm transition-opacity duration-300"
      style={{ opacity: isActive || isCompleted ? 1 : 0.4 }}
    >
      {isCompleted ? (
        <Check className="w-[1.2vh] h-[1.2vh] text-gray-500 stroke-[4px]" />
      ) : isActive ? (
        <Loader2 className="w-[1.2vh] h-[1.2vh] text-gray-600 animate-spin" />
      ) : (
        <div className="w-[0.5vh] h-[0.5vh] rounded-full bg-gray-200" />
      )}
    </div>
  );
};
