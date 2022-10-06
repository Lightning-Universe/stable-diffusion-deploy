import CopyAllRoundedIcon from '@mui/icons-material/CopyAllRounded';
import { Box, IconButton } from '@mui/material';
import { getAndroidVersion } from 'hooks/usePlatform';
import { useSnackbar } from 'lightning-ui/src/design-system/components';
import { useMemo } from 'react';

export const DownloadImageButton = (props: { imgResult: string | null }) => {
  const { enqueueSnackbar } = useSnackbar();

  const handleCopyImage = () => {
    if (!props.imgResult) return;
    copyImageToClipboard(props.imgResult);
    enqueueSnackbar({
      title: 'Image copied',
      severity: 'success',
    });
  };
  const androidVersion = useMemo(() => getAndroidVersion(), []);

  const disabled = !props.imgResult;
  return (
    <Box
      sx={{
        display: androidVersion === 0 ? 'block' : 'none',
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 8,
        borderRadius: 40,
        background: disabled ? '#E4E6EB' : '#FFFFFFBF',
        boxShadow: 'inset 0px 0px 0px 20px rgba(255, 255, 255, 0.3)',
      }}>
      <IconButton onClick={handleCopyImage} disabled={disabled}>
        <CopyAllRoundedIcon style={{ color: disabled ? '#C5CBD7' : '#1C1C1C' }} />
      </IconButton>
    </Box>
  );
};

const copyImageToClipboard = async (content: string) => {
  const blobToClipboard = (content: string | Promise<Blob> | Blob) => {
    try {
      navigator.clipboard.write([new ClipboardItem({ 'image/png': content })]);
    } catch (e) {
      console.warn(e);
    }
  };

  // todo: add better error handler
  if (content.startsWith('/static')) {
    const imgContent = await (await fetch(content)).blob();
    blobToClipboard(imgContent);
    return;
  }
  blobToClipboard(content);
};
