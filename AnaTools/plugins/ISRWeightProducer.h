#ifndef ISR_WEIGHT_PRODUCER
#define ISR_WEIGHT_PRODUCER

#include "OSUT3Analysis/AnaTools/interface/EventVariableProducer.h"

#include "TH1D.h"
#include "TFile.h"

class ISRWeightProducer : public EventVariableProducer
{
public:
  ISRWeightProducer(const edm::ParameterSet &);
  ~ISRWeightProducer();

private:
  edm::EDGetTokenT<vector<TYPE(hardInteractionMcparticles)> > mcparticlesToken_;

  vector<int> pdgIds_;
  string weightFile_;
  string weightHist_;

  TH1D *weights_;

  bool isOriginalParticle (const TYPE(hardInteractionMcparticles) &, const int) const;
  void AddVariables(const edm::Event &);
};

#endif
