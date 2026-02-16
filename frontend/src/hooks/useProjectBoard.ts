/**
 * Custom hook for project board data fetching and state management.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectBoardApi } from '@/services/api';
import type { BoardIssueCard } from '@/types';

export function useProjectBoard() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState<BoardIssueCard | null>(null);

  // Fetch project list
  const {
    data: projectsData,
    isLoading: projectsLoading,
    isError: projectsError,
    error: projectsErrorObj,
    refetch: refetchProjects,
  } = useQuery({
    queryKey: ['board-projects'],
    queryFn: () => projectBoardApi.listProjects(),
  });

  // Fetch board data for selected project
  const {
    data: boardData,
    isLoading: boardLoading,
    isError: boardError,
    error: boardErrorObj,
    isFetching: boardFetching,
    refetch: refetchBoard,
  } = useQuery({
    queryKey: ['board-data', selectedProjectId],
    queryFn: () => projectBoardApi.getBoardData(selectedProjectId!),
    enabled: !!selectedProjectId,
    refetchInterval: isModalOpen ? false : 15000,
    staleTime: 10000,
  });

  const selectProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setSelectedCard(null);
    setIsModalOpen(false);
  };

  const openModal = (card: BoardIssueCard) => {
    setSelectedCard(card);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedCard(null);
  };

  return {
    // Project list
    projects: projectsData?.projects ?? [],
    projectsLoading,
    projectsError,
    projectsErrorObj,
    refetchProjects,

    // Board data
    selectedProjectId,
    boardData,
    boardLoading,
    boardError,
    boardErrorObj,
    boardFetching,
    refetchBoard,

    // Modal state
    isModalOpen,
    selectedCard,

    // Actions
    selectProject,
    openModal,
    closeModal,
  };
}
