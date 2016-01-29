#ifndef OSU_MUON
#define OSU_MUON

#include "OSUT3Analysis/Collections/interface/GenMatchable.h"

#if IS_VALID(muons)

#if DATA_FORMAT == MINI_AOD || DATA_FORMAT == MINI_AOD_CUSTOM || DATA_FORMAT == AOD
namespace osu
{
  class Muon : public GenMatchable<TYPE(muons), 13>
    {
      public:
        Muon ();
        Muon (const TYPE(muons) &);
        Muon (const TYPE(muons) &, const edm::Handle<vector<osu::Mcparticle> > &);
        Muon (const TYPE(muons) &, const edm::Handle<vector<osu::Mcparticle> > &, const edm::ParameterSet &);
        ~Muon ();

        const bool isTightMuonWRTVtx() const { return isTightMuonWRTVtx_; }
        void   set_isTightMuonWRTVtx(const bool isTightMuon);

      private:
        bool isTightMuonWRTVtx_;

    };
}
#elif DATA_FORMAT == AOD_CUSTOM
namespace osu
{
  class Muon : public TYPE(muons)
    {
      public:
        Muon ();
        Muon (const TYPE(muons) &);
        ~Muon ();
    };
}
#endif

#else

namespace osu
{
  typedef TYPE(muons) Muon;
}

#endif

#endif
