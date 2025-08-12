import { Helmet } from "react-helmet-async";
import { useLocation } from "react-router-dom";

type SeoProps = {
  title: string;
  description?: string;
};

const Seo = ({ title, description }: SeoProps) => {
  const { pathname } = useLocation();
  const canonical = typeof window !== "undefined" ? window.location.origin + pathname : pathname;
  const metaDesc = description ?? "Automated, exam-ready study material generation for colleges.";

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={metaDesc} />
      <link rel="canonical" href={canonical} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={metaDesc} />
    </Helmet>
  );
};

export default Seo;
