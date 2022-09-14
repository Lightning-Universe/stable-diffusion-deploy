import { Typography as MuiTypography, TypographyProps } from '@mui/material';

export const Typography = (props: TypographyProps) => {
  return <MuiTypography color={(theme: any) => theme.palette.grey['70']} {...props} />;
};
