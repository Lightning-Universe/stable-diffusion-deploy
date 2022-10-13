import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded';
import { Box, IconButton } from '@mui/material';

export const DownloadImageButton = (props: { imgResult: string | null; query: string }) => {
  const handleCopyImage = () => {
    downloadImage(`${props.query}.png`);
  };

  const disabled = !props.imgResult;
  return (
    <Box
      sx={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 8,
        borderRadius: 40,
        background: disabled ? '#E4E6EB' : '#FFFFFFBF',
        boxShadow: 'inset 0px 0px 0px 20px rgba(255, 255, 255, 0.3)',
      }}>
      <IconButton onClick={handleCopyImage} disabled={disabled}>
        <DownloadRoundedIcon style={{ color: disabled ? '#C5CBD7' : '#1C1C1C' }} />
      </IconButton>
      {/* only to test, this does not render anything to the screen */}
      <a href={props.imgResult!} download={props.query} children={''} target={'_blank'} rel={'noreferrer'} />
    </Box>
  );
};

const downloadImage = async (name: string = 'image.png') => {
  const image = document.getElementById('imgResult') as HTMLImageElement;
  if (!image) return;
  downloadURI(image.src, name);
};

function downloadURI(uri: string, name: string) {
  const link = document.createElement('a');
  link.href = uri;
  link.download = name;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  link.remove();
}
