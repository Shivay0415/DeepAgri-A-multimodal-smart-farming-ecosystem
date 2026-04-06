function PageHero({ eyebrow, title, description, accent = "soil", children }) {
  return (
    <section className={`page-hero page-hero--${accent}`}>
      <div className="page-hero__content">
        <p className="page-hero__eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-hero__description">{description}</p>
      </div>
      {children ? <div className="page-hero__aside">{children}</div> : null}
    </section>
  );
}

export default PageHero;
