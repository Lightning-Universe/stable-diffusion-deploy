import { useSnackbar } from 'lightning-ui/src/design-system/components';

export const copyToClipboard = (text: string) => {
  window.navigator?.clipboard?.writeText(text);
};

export const useClipboard = () => {
  const { enqueueSnackbar } = useSnackbar();

  return (text?: string) => {
    if (!text) return;
    copyToClipboard(text);
    enqueueSnackbar({ severity: 'success', title: 'Copied to clipboard!' });
  };
};
