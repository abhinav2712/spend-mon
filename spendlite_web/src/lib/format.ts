const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatINR = (value: number): string => inr.format(value);

export const titleCase = (s: string): string => s.charAt(0).toUpperCase() + s.slice(1);
