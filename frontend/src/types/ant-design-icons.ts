import type { ComponentType, CSSProperties, SVGProps } from 'react';

type AntdIconProps = SVGProps<SVGSVGElement> & {
  className?: string;
  rotate?: number;
  spin?: boolean;
  style?: CSSProperties;
  twoToneColor?: string;
};

type AntdIconComponent = ComponentType<AntdIconProps>;

export declare const ArrowLeftOutlined: AntdIconComponent;
export declare const CheckOutlined: AntdIconComponent;
export declare const CodeOutlined: AntdIconComponent;
export declare const DeleteOutlined: AntdIconComponent;
export declare const EditOutlined: AntdIconComponent;
export declare const ExperimentOutlined: AntdIconComponent;
export declare const FileMarkdownOutlined: AntdIconComponent;
export declare const FilePdfOutlined: AntdIconComponent;
export declare const FileTextOutlined: AntdIconComponent;
export declare const HomeOutlined: AntdIconComponent;
export declare const LoadingOutlined: AntdIconComponent;
export declare const LockOutlined: AntdIconComponent;
export declare const LogoutOutlined: AntdIconComponent;
export declare const MailOutlined: AntdIconComponent;
export declare const MoreOutlined: AntdIconComponent;
export declare const PlusOutlined: AntdIconComponent;
export declare const ReloadOutlined: AntdIconComponent;
export declare const SearchOutlined: AntdIconComponent;
export declare const SettingOutlined: AntdIconComponent;
export declare const ShareAltOutlined: AntdIconComponent;
export declare const UserOutlined: AntdIconComponent;
