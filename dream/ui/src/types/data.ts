export type Argument = {
  name: string;
  label: string;
  type: 'string' | 'file' | 'folder';
};

export type Format = {
  name: string;
  label: string;
  arguments: Argument[];
};

export type DataOptions = {
  task: string;
  label: string;
  formats: Format[];
};

export type Demo = {
  // name: string;
  // label: string;
  task: string;
  config: Map<string, any>;
};
