export const TelemetryProvider = ({ children }: { children: ReactNode }) => {
  const [riskScore, setRiskScore] = useState<number>(0);

  // Create the context value object
  const value = {
    riskScore,
    setRiskScore,
  };

  return (
    <TelemetryContext.Provider value={value}>
      {children}
    </TelemetryContext.Provider>
  );
};