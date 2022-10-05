import { Typography as MuiTypography, TypographyProps } from '@mui/material';

export const Typography = ({
  colorI = 'secondary',
  ...props
}: TypographyProps & { colorI?: 'primary' | 'secondary'; fontFamily?: 'Roboto' | 'UCity' }) => {
  return (
    <MuiTypography
      fontFamily={props.fontFamily ?? 'Roboto'}
      color={(theme: any) => (colorI === 'primary' ? theme.palette.text.primary : theme.palette.grey['70'])}
      {...props}
      style={{ textTransform: 'none' }}
    />
  );
};
