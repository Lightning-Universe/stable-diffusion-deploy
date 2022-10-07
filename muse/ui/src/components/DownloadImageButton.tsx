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
      title: 'Image copied to clipboard.',
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
  const image = document.getElementById('imgResult') as HTMLImageElement;

  if (!image) return;

  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext('2d');
  context!.drawImage(image, 0, 0);

  canvas.toBlob(blob => {
    if (!blob) return;
    navigator.clipboard
      .write([
        new ClipboardItem({
          [blob.type]: blob,
        }),
      ])
      .then(() => {
        console.log('Copied');
      });
  });
};
