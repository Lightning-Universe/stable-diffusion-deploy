import { useState } from 'react';

export const useDialogState = (initial = false) => {
  // should be isOpen
  const [open, setIsOpen] = useState(initial);
  const onClose = () => setIsOpen(false);
  const onOpen = () => setIsOpen(true);
  return { open, onClose, onOpen };
};
