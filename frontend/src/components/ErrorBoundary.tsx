import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("FieldworkTools error boundary caught:", error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{ padding: 32, textAlign: "center" }}>
          <h3 style={{ color: "#DC2626", marginBottom: 12 }}>
            ⚠ 工具箱出错
          </h3>
          <p style={{ color: "#6B7280", marginBottom: 16, fontSize: 14 }}>
            {this.state.error?.message || "发生了未预期的错误，请刷新页面重试。"}
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: "10px 24px",
              background: "#1E3A8A",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
